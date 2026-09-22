from backend.services.data import dates, records


def exceptions(shipments, inventory, suppliers):
    alerts = []
    for row in inventory:
        if row["risk"] in ["High", "Medium"]:
            alerts.append(
                {
                    "id": "inventory-" + row["id"],
                    "type": "Inventory",
                    "severity": row["risk"],
                    "object": row["sku"] + " · " + row["location"],
                    "trigger": f"{row['days_of_supply']:.1f} days of supply; {row['forecast_demand']:,.0f} units forecast in 28 days.",
                    "kpi": "Stockout risk / service level",
                    "impact": f"{row['shortage']:,.0f} projected units short"
                    if row["shortage"]
                    else "Safety-stock buffer at risk",
                    "action": row["action"],
                    "expected_impact": "Improve projected stock coverage; validate transfer lead time and donor availability.",
                    "page": "Inventory",
                    "reference": row["id"],
                    "replay": False,
                    "score": 100 if row["risk"] == "High" else 60,
                }
            )
    for row in shipments:
        if row["risk"] == "High":
            alerts.append(
                {
                    "id": "delay-" + row["id"],
                    "type": "Transportation",
                    "severity": "High",
                    "object": row["shipment_number"],
                    "trigger": f"{row['late_probability']:.0%} estimated late probability · +{row['predicted_delay']:.1f} h predicted delay",
                    "kpi": "On-time delivery",
                    "impact": row["orders"],
                    "action": "Review carrier and customer promise; compare expedited service in Scenario Analysis.",
                    "expected_impact": "Earlier review may protect service commitments; benefit is not quantified.",
                    "page": "Transportation",
                    "reference": row["id"],
                    "replay": True,
                    "score": row["late_probability"] * 90,
                }
            )
        if row["anomaly"]:
            alerts.append(
                {
                    "id": "anomaly-" + row["id"],
                    "type": "Anomaly",
                    "severity": "Medium",
                    "object": row["shipment_number"],
                    "trigger": f"Isolation Forest flagged this completed shipment; cost/km {row['cost_ratio']:.2f}× median for its mode and service."
                    if row["cost_ratio"]
                    else "Unusual completed shipment.",
                    "kpi": "Freight cost / transit variability",
                    "impact": f"{row['freight_cost_sek']:,.0f} SEK freight cost to review",
                    "action": "Review invoice, load and route context. Anomaly is a review signal, not evidence of error.",
                    "expected_impact": "Identify potential cost or service exceptions; no savings assumed.",
                    "page": "Transportation",
                    "reference": row["id"],
                    "replay": True,
                    "score": 40 + row["anomaly_score"],
                }
            )
    for row in suppliers:
        if row["risk"] == "High":
            alerts.append(
                {
                    "id": "supplier-" + row["id"],
                    "type": "Supplier",
                    "severity": "Medium",
                    "object": row["name"],
                    "trigger": f"{row['late_probability']:.0%} mean predicted late probability on held-out purchase orders.",
                    "kpi": "Supplier on-time delivery",
                    "impact": f"Historical OTD {row['on_time']:.1f}% against requested date",
                    "action": row["action"],
                    "expected_impact": "Review replenishment lead-time buffers; no causal improvement assumed.",
                    "page": "Suppliers",
                    "reference": row["id"],
                    "replay": True,
                    "score": 50,
                }
            )
    return sorted(alerts, key=lambda a: (a["severity"] == "High", a["score"]), reverse=True)


def overview(tables, bundle, shipments, inventory, supplier_rows, production, alerts, source):
    s = tables["shipments"].copy()
    delivered = s[
        dates(s.actual_arrival_at).notna() & ~s.status.isin(["CANCELLED", "CANCELED"])
    ].copy()
    delivered["on_time"] = dates(delivered.actual_arrival_at) <= dates(delivered.planned_arrival_at)
    delivered["transit"] = (
        dates(delivered.actual_arrival_at) - dates(delivered.actual_departure_at)
    ).dt.total_seconds() / 3600
    delivered["month"] = dates(delivered.planned_arrival_at).dt.strftime("%Y-%m")
    trend = (
        delivered.groupby("month")
        .agg(
            on_time=("on_time", "mean"),
            shipments=("id", "count"),
            freight=("freight_cost_sek", "sum"),
        )
        .reset_index()
    )
    trend.on_time *= 100
    forecasts = bundle["forecasts"]
    wape = next(c["metrics"]["wape"] for c in bundle["cards"] if c["id"] == "demand")
    supplier_count = sum(r["orders"] for r in supplier_rows)
    kpis = [
        {
            "label": "On-time delivery",
            "value": float(delivered.on_time.mean() * 100),
            "unit": "%",
            "detail": f"{len(delivered):,} completed shipments",
            "definition": "Actual arrival ≤ planned arrival, divided by completed non-cancelled shipments. Strict zero-hour tolerance.",
            "tone": "teal",
        },
        {
            "label": "Shipment delay rate",
            "value": float((1 - delivered.on_time.mean()) * 100),
            "unit": "%",
            "detail": "Historical delivery outcomes",
            "definition": "Complement of on-time delivery for the same completed shipment cohort.",
            "tone": "amber",
        },
        {
            "label": "Projected shortages",
            "value": sum(r["risk"] == "High" for r in inventory),
            "unit": "positions",
            "detail": "28-day inventory projection",
            "definition": "SKU-location positions with a negative projected balance on any day. Unscored components excluded.",
            "tone": "red",
        },
        {
            "label": "Freight spend",
            "value": float(delivered.freight_cost_sek.sum()),
            "unit": "SEK",
            "detail": "Completed shipment history",
            "definition": "Sum of freight_cost_sek on completed non-cancelled shipments.",
            "tone": "blue",
        },
        {
            "label": "Supplier on-time",
            "value": sum(r["on_time"] * r["orders"] for r in supplier_rows) / supplier_count
            if supplier_count
            else None,
            "unit": "%",
            "detail": "Against original requested date",
            "definition": "Completed purchase orders received by requested date; weighted by order count.",
            "tone": "teal",
        },
        {
            "label": "Forecast WAPE",
            "value": wape * 100 if wape is not None else None,
            "unit": "%",
            "detail": "8-week holdout · lower is better",
            "definition": "Sum of absolute forecast errors ÷ actual demand across SKU holdouts.",
            "tone": "blue",
        },
        {
            "label": "Average transit",
            "value": float(delivered.transit.mean()),
            "unit": "h",
            "detail": "Actual departure → arrival",
            "definition": "Mean completed shipment transit duration in hours.",
            "tone": "blue",
        },
        {
            "label": "Capacity utilization",
            "value": production["utilization"],
            "unit": "%",
            "detail": "Actual / planned capacity units",
            "definition": production["definition"],
            "tone": "teal",
        },
    ]
    inventory_total = sum(r["inventory_value"] for r in inventory)
    scored = [r for r in inventory if r["risk"] != "Not scored"]
    quality = [
        {
            "check": "Completed shipment history",
            "value": len(delivered),
            "note": "All supplied shipments are delivered. Risk screens replay the unseen test period.",
        },
        {
            "check": "Demand coverage",
            "value": len(forecasts),
            "note": "Finished-goods SKUs forecast from sales orders; components need BOM-dependent demand.",
        },
        {
            "check": "Scored inventory positions",
            "value": len(scored),
            "note": f"{len(inventory) - len(scored)} positions have no independent demand/location history and are not scored.",
        },
        {
            "check": "Missing shipment planning fields",
            "value": int(
                s[["planned_departure_at", "planned_arrival_at", "distance_km", "total_weight_kg"]]
                .isna()
                .any(axis=1)
                .sum()
            ),
            "note": "Rows with invalid outcomes are excluded from supervised training.",
        },
        {
            "check": "Negative available inventory",
            "value": int((tables["inventory_balances"].available_quantity < 0).sum()),
            "note": "Negative inventory requires operational review.",
        },
    ]
    locations = records(
        tables["locations"][["id", "name", "city", "location_type", "latitude", "longitude"]]
    )
    lanes = (
        s.groupby(["origin_location_id", "destination_location_id"])
        .size()
        .reset_index(name="shipments")
        .sort_values("shipments", ascending=False)
        .head(35)
    )
    return {
        "source": source,
        "as_of": str(dates(tables["inventory_balances"].as_of_timestamp).max()),
        "history_from": str(dates(delivered.planned_departure_at).min()),
        "history_to": str(dates(delivered.actual_arrival_at).max()),
        "kpis": kpis,
        "trend": records(trend),
        "quality": quality,
        "locations": locations,
        "lanes": records(lanes),
        "counts": {
            "shipments": len(s),
            "replay_shipments": len(shipments),
            "high_delay": sum(r["risk"] == "High" for r in shipments),
            "shortages": sum(r["risk"] == "High" for r in inventory),
            "anomalies": sum(r["anomaly"] for r in shipments),
            "suppliers": len(supplier_rows),
            "exceptions": len(alerts),
            "inventory_value": inventory_total,
        },
        "risk_distribution": [
            {"name": risk, "count": sum(r["risk"] == risk for r in shipments)}
            for risk in ["Low", "Medium", "High"]
        ],
        "limitations": [
            "Historical synthetic dataset, not a live operational feed.",
            "Delay and supplier classifiers have weak holdout ranking performance; probabilities are uncalibrated.",
            "Inventory projection reuses the latest weekly demand level at the balance snapshot date; it does not assume missing weeks had zero demand.",
            "OTIF and inventory turnover are omitted: consistent order-completion timestamps and a matching average-inventory/COGS period are not established.",
        ],
    }
