"""Forecast-driven stock projection; this is not a supervised stockout classifier."""

import math

import pandas as pd

from backend.services.data import records


def project(available, daily_demand, inbound, horizon=28, safety_stock=0):
    balance = float(available)
    shortage_day = None
    trajectory = []
    for day in range(1, horizon + 1):
        balance += sum(float(item["quantity"]) for item in inbound if item["day"] == day)
        balance -= daily_demand
        if balance < 0 and shortage_day is None:
            shortage_day = day
        trajectory.append({"day": day, "balance": round(balance, 2)})
    peak_shortage = max(0, -min(point["balance"] for point in trajectory))
    return {
        "projected_balance": round(balance, 2),
        "shortage": round(peak_shortage, 2),
        "shortage_day": shortage_day,
        "trajectory": trajectory,
        "risk": "High" if shortage_day else ("Medium" if balance < safety_stock else "Low"),
        "days_of_supply": round(max(0, available) / daily_demand, 1) if daily_demand > 0 else None,
    }


def inventory_risks(tables, forecasts):
    products = tables["products"].set_index("id")
    locations = tables["locations"].set_index("id")
    forecast_map = {f["product_id"]: f for f in forecasts}
    po = tables["purchase_orders"]
    inbound = tables["purchase_order_lines"].merge(
        po[["id", "destination_location_id", "confirmed_delivery_date", "status"]],
        left_on="purchase_order_id",
        right_on="id",
        suffixes=("", "_order"),
    )
    inbound = inbound[~inbound.status_order.isin(["RECEIVED", "CANCELLED", "CANCELED"])]
    transfers = tables["transfer_order_lines"].merge(
        tables["transfer_orders"][
            ["id", "destination_location_id", "required_arrival_date", "status"]
        ],
        left_on="transfer_order_id",
        right_on="id",
        suffixes=("", "_order"),
    )
    transfers = transfers[~transfers.status.isin(["RECEIVED", "CANCELLED", "CANCELED"])]
    rows = []
    for row in records(tables["inventory_balances"]):
        pid, lid = row["product_id"], row["location_id"]
        product, location = products.loc[pid], locations.loc[lid]
        forecast = forecast_map.get(pid)
        share = forecast["location_shares"].get(lid, 0) if forecast else 0
        daily = forecast["weekly"] * share / 7 if forecast and share else None
        anchor = pd.Timestamp(row["as_of_timestamp"])
        incoming = []
        for candidate in records(
            inbound[(inbound.product_id == pid) & (inbound.destination_location_id == lid)]
        ):
            due = pd.to_datetime(candidate["confirmed_delivery_date"], utc=True)
            day = max(1, (due - anchor).days + 1) if pd.notna(due) else 0
            qty = max(
                0,
                float(candidate["confirmed_quantity"] or 0)
                - float(candidate["received_quantity"] or 0),
            )
            if 1 <= day <= 28 and due >= anchor and qty:
                incoming.append({"day": day, "quantity": qty})
        for candidate in records(
            transfers[(transfers.product_id == pid) & (transfers.destination_location_id == lid)]
        ):
            due = pd.to_datetime(candidate["required_arrival_date"], utc=True)
            day = max(1, (due - anchor).days + 1) if pd.notna(due) else 0
            qty = max(0, candidate["shipped_quantity"] - candidate["received_quantity"])
            if 1 <= day <= 28 and due >= anchor and qty:
                incoming.append({"day": day, "quantity": qty})
        projection = project(
            row["available_quantity"],
            daily or 0,
            incoming,
            safety_stock=row["safety_stock_quantity"],
        )
        if daily is None:
            projection.update(
                risk="Not scored",
                days_of_supply=None,
                shortage=None,
                projected_balance=None,
                shortage_day=None,
            )
        rows.append(
            {
                **projection,
                "id": row["id"],
                "product_id": pid,
                "location_id": lid,
                "sku": product.sku,
                "product": product["name"],
                "location": location["name"],
                "available": row["available_quantity"],
                "on_hand": row["on_hand_quantity"],
                "safety_stock": row["safety_stock_quantity"],
                "reorder_point": row["reorder_point_quantity"],
                "inventory_value": row["on_hand_quantity"] * product.unit_cost_sek,
                "unit_cost": product.unit_cost_sek,
                "forecast_demand": round(daily * 28, 2) if daily is not None else None,
                "daily_demand": daily,
                "incoming": sum(i["quantity"] for i in incoming),
                "inbound_schedule": incoming,
                "excess": daily is not None
                and row["available_quantity"] > daily * 56 + row["safety_stock_quantity"],
                "as_of": anchor.isoformat(),
                "forecast_origin": forecast["future"][0]["week"] if forecast else None,
                "method": "28-day deterministic projection using SKU forecast × recent warehouse demand share. Confirmed dated receipts counted once; undated in-transit excluded. Components without independent demand are not scored.",
                "action": "Review replenishment or an internal transfer."
                if projection["risk"] == "High"
                else (
                    "Review safety-stock buffer."
                    if projection["risk"] == "Medium"
                    else "Monitor coverage and review excess stock."
                ),
            }
        )
    # Candidate transfers are independent alternatives, not a jointly feasible allocation plan.
    for row in rows:
        row["transfer"] = None
        if row["risk"] != "High":
            continue
        donors = [
            r
            for r in rows
            if r["product_id"] == row["product_id"]
            and r["location_id"] != row["location_id"]
            and r["daily_demand"] is not None
        ]
        for donor in sorted(donors, key=lambda r: r["available"], reverse=True):
            spare = max(0, donor["available"] - donor["forecast_demand"] - donor["safety_stock"])
            amount = min(math.ceil(row["shortage"] + row["safety_stock"]), math.floor(spare))
            if amount > 0:
                row["transfer"] = {
                    "from": donor["location"],
                    "quantity": amount,
                    "days_before": row["days_of_supply"],
                    "days_after": round((row["available"] + amount) / row["daily_demand"], 1),
                }
                row["action"] = (
                    f"Review transfer of {amount:,.0f} units from {donor['location']}; confirm arrival before day {row['shortage_day']}."
                )
                break
    return sorted(
        rows,
        key=lambda r: (
            {"High": 0, "Medium": 1, "Low": 2, "Not scored": 3}[r["risk"]],
            r["days_of_supply"] or 1e9,
        ),
    )


def scenario(row, demand_change, replenishment, lead_days, safety_stock):
    if row["daily_demand"] is None:
        raise ValueError("This position has no independent demand forecast.")
    daily = row["daily_demand"] * (1 + demand_change / 100)
    incoming = list(row["inbound_schedule"])
    if replenishment and 1 <= lead_days <= 28:
        incoming.append({"day": lead_days, "quantity": replenishment})
    baseline = project(
        row["available"],
        row["daily_demand"],
        row["inbound_schedule"],
        safety_stock=row["safety_stock"],
    )
    result = project(row["available"], daily, incoming, safety_stock=safety_stock)
    return {
        "baseline": baseline,
        "scenario": result,
        "incremental_inventory_value": replenishment * row["unit_cost"],
        "demand_change": demand_change,
        "replenishment": replenishment,
        "lead_days": lead_days,
        "assumptions": "Uniform daily demand; receipt arrives at start of selected day. Negative balance represents backlog. Days of supply uses current available inventory only. Replenishment after day 28 cannot prevent a shortage in this horizon. Safety stock changes the warning threshold, not physical supply.",
    }
