import numpy as np

from backend.ml.features import supplier_features
from backend.services.data import dates, records


def suppliers(tables, bundle):
    purchase = tables["purchase_orders"].copy()
    purchase = purchase[
        dates(purchase.actual_delivery_date).notna()
        & ~purchase.status.isin(["CANCELLED", "CANCELED"])
    ]
    purchase["on_time"] = dates(purchase.actual_delivery_date) <= dates(
        purchase.requested_delivery_date
    )
    purchase["lead_days"] = (
        dates(purchase.actual_delivery_date) - dates(purchase.order_date)
    ).dt.days
    cutoff = next((c["cutoff"] for c in bundle["cards"] if c["id"] == "supplier"), None)
    holdout = (
        purchase[dates(purchase.order_date) >= cutoff].copy()
        if cutoff
        else purchase.iloc[:0].copy()
    )
    if "supplier" in bundle["models"]:
        holdout["predicted_late"] = bundle["models"]["supplier"].predict_proba(
            supplier_features(holdout)
        )[:, 1]
    else:
        holdout["predicted_late"] = np.nan
    org = tables["organizations"].set_index("id")
    rows = []
    for supplier, group in purchase.groupby("supplier_id"):
        lines = tables["purchase_order_lines"][
            tables["purchase_order_lines"].purchase_order_id.isin(group.id)
        ]
        received = float(lines.received_quantity.sum())
        ordered = float(lines.ordered_quantity.sum())
        risk = holdout[holdout.supplier_id == supplier].predicted_late.mean()
        rows.append(
            {
                "id": supplier,
                "name": org.loc[supplier, "name"],
                "country": org.loc[supplier, "country_code"],
                "orders": len(group),
                "on_time": float(group.on_time.mean() * 100),
                "lead_days": float(group.lead_days.mean()),
                "fill_rate": received / ordered * 100 if ordered else None,
                "rejection_rate": float(lines.rejected_quantity.sum()) / received * 100
                if received
                else None,
                "late_probability": float(risk) if np.isfinite(risk) else None,
                "risk": "High" if risk >= 0.5 else "Medium" if risk >= 0.3 else "Low",
                "action": "Review earlier ordering and approved sourcing alternatives; historical risk scores have limited discrimination.",
            }
        )
    return rows


def production(tables):
    orders = tables["production_orders"].copy()
    capacity = tables["production_capacity"].copy()
    planned = float(orders.planned_quantity.sum())
    produced = float(orders.produced_quantity.sum())
    capacity["month"] = dates(capacity.capacity_date).dt.strftime("%Y-%m")
    monthly = (
        capacity.groupby("month")
        .agg(
            planned=("planned_capacity_units", "sum"),
            actual=("actual_capacity_units", "sum"),
            downtime=("downtime_minutes", "sum"),
        )
        .reset_index()
    )
    monthly["utilization"] = monthly.actual / monthly.planned.replace(0, np.nan) * 100
    locations = tables["locations"].set_index("id")["name"].to_dict()
    products = tables["products"].set_index("id")["name"].to_dict()
    orders["plant"] = orders.plant_location_id.map(locations)
    orders["product"] = orders.product_id.map(products)
    return {
        "plan_attainment": produced / planned * 100 if planned else None,
        "scrap_rate": float(orders.scrapped_quantity.sum()) / produced * 100 if produced else None,
        "utilization": float(
            capacity.actual_capacity_units.sum() / capacity.planned_capacity_units.sum() * 100
        )
        if capacity.planned_capacity_units.sum()
        else None,
        "late_rate": float(
            (dates(orders.actual_end_at) > dates(orders.planned_end_at)).mean() * 100
        ),
        "downtime_hours": float(capacity.downtime_minutes.sum() / 60),
        "monthly": records(monthly),
        "orders": records(
            orders.sort_values("planned_start_at", ascending=False).head(100)[
                [
                    "production_order_number",
                    "plant",
                    "product",
                    "planned_quantity",
                    "produced_quantity",
                    "scrapped_quantity",
                    "status",
                ]
            ]
        ),
        "definition": "Historical actual capacity units ÷ planned capacity units; plan attainment is produced ÷ planned order quantity. No future capacity calendar exists, so future capacity gaps are not inferred.",
    }
