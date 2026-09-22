import numpy as np
import pandas as pd

from backend.ml.features import shipment_features
from backend.services.data import dates, records


def shipment_risks(tables, bundle):
    source = tables["shipments"].copy()
    cutoff = next(c["cutoff"] for c in bundle["cards"] if c["id"] == "delay")
    # Replay only held-out shipments, avoiding misleading in-sample prediction demonstrations.
    frame = source[dates(source.planned_departure_at) >= pd.Timestamp(cutoff)].copy()
    features = shipment_features(frame)
    frame["late_probability"] = bundle["models"]["delay"].predict_proba(features)[:, 1]
    frame["predicted_delay"] = np.maximum(0, bundle["models"]["eta"].predict(features))
    frame["predicted_cost"] = np.maximum(0, bundle["models"]["cost"].predict(features))
    frame["target_delay"] = (
        (dates(frame.actual_arrival_at) - dates(frame.planned_arrival_at)).dt.total_seconds() / 3600
    ).clip(lower=0)
    anomaly_cols = [
        "freight_cost_sek",
        "distance_km",
        "total_weight_kg",
        "total_volume_m3",
        "target_delay",
    ]
    frame["anomaly"] = bundle["models"]["anomaly"].predict(frame[anomaly_cols]) == -1
    frame["anomaly_score"] = -bundle["models"]["anomaly"].decision_function(frame[anomaly_cols])
    locations = tables["locations"].set_index("id")["name"].to_dict()
    carriers = tables["organizations"].set_index("id")["name"].to_dict()
    for col in ["origin", "destination"]:
        frame[col] = frame[f"{col}_location_id"].map(locations)
    frame["carrier"] = frame.carrier_id.map(carriers)
    frame["risk"] = np.select(
        [frame.late_probability >= 0.5, frame.late_probability >= 0.3],
        ["High", "Medium"],
        default="Low",
    )
    frame["predicted_eta"] = dates(frame.planned_arrival_at) + pd.to_timedelta(
        frame.predicted_delay, unit="h"
    )
    peers = (
        source.assign(cost_per_km=source.freight_cost_sek / source.distance_km.replace(0, np.nan))
        .groupby(["transport_mode", "service_level"])
        .cost_per_km.median()
    )
    frame["cost_ratio"] = [
        float(
            (r.freight_cost_sek / r.distance_km)
            / peers.get((r.transport_mode, r.service_level), np.nan)
        )
        if r.distance_km
        else None
        for r in frame.itertuples()
    ]
    # Trace shipment → customer order using real shipment-item relationships.
    lines = tables["shipment_items"].merge(
        tables["sales_order_lines"][["id", "sales_order_id"]],
        left_on="sales_order_line_id",
        right_on="id",
    )
    lines = lines.merge(
        tables["sales_orders"][["id", "order_number", "priority", "customer_id"]],
        left_on="sales_order_id",
        right_on="id",
        suffixes=("", "_order"),
    )
    linked = (
        lines.groupby("shipment_id")
        .agg(
            orders=("order_number", lambda x: ", ".join(sorted(set(x)))),
            priority=("priority", lambda x: ", ".join(sorted(set(x)))),
        )
        .to_dict("index")
    )
    rows = []
    columns = [
        "id",
        "shipment_number",
        "transport_mode",
        "service_level",
        "status",
        "origin",
        "destination",
        "carrier",
        "carrier_id",
        "origin_location_id",
        "destination_location_id",
        "planned_departure_at",
        "planned_arrival_at",
        "actual_arrival_at",
        "current_eta",
        "late_probability",
        "predicted_delay",
        "predicted_eta",
        "predicted_cost",
        "freight_cost_sek",
        "distance_km",
        "total_weight_kg",
        "total_volume_m3",
        "target_delay",
        "risk",
        "anomaly",
        "anomaly_score",
        "cost_ratio",
    ]
    for row in records(frame.sort_values("late_probability", ascending=False)[columns]):
        row.update(linked.get(row["id"], {"orders": "No linked customer order", "priority": "—"}))
        row["context"] = [
            f"{row['transport_mode']} · {row['service_level']}",
            f"{row['distance_km']:,.0f} km planned route",
            row["carrier"],
        ]
        rows.append(row)
    return rows


def predict_transport(tables, bundle, shipment_id, changes):
    matched = tables["shipments"][tables["shipments"].id == shipment_id]
    if matched.empty:
        raise KeyError("Unknown shipment")
    base = matched.copy()
    modified = base.copy()
    for key, value in changes.items():
        if value is not None:
            modified[key] = value

    def score(frame):
        x = shipment_features(frame)
        cost = max(0, float(bundle["models"]["cost"].predict(x)[0]))
        return {
            "cost": round(cost, 2),
            "cost_per_km": round(cost / float(frame.distance_km.iloc[0]), 2),
            "late_probability": float(bundle["models"]["delay"].predict_proba(x)[0, 1]),
            "delay_hours": max(0, float(bundle["models"]["eta"].predict(x)[0])),
        }

    result = score(modified)
    comparables = tables["shipments"]
    comparables = comparables[
        (comparables.transport_mode == modified.transport_mode.iloc[0])
        & (comparables.service_level == modified.service_level.iloc[0])
    ]
    result["historical_average"] = (
        float(comparables.freight_cost_sek.mean()) if len(comparables) else None
    )
    result["comparable_count"] = len(comparables)
    bounds = []
    observed = tables["shipments"]
    combination = observed[
        (observed.transport_mode == modified.transport_mode.iloc[0])
        & (observed.service_level == modified.service_level.iloc[0])
        & (observed.carrier_id == modified.carrier_id.iloc[0])
    ]
    if combination.empty:
        bounds.append(
            "This mode, service and carrier combination was not observed in the source data. Treat the estimate as extrapolation."
        )
    for col in ["distance_km", "total_weight_kg", "total_volume_m3"]:
        low, high = float(tables["shipments"][col].min()), float(tables["shipments"][col].max())
        if not low <= float(modified[col].iloc[0]) <= high:
            bounds.append(f"{col} outside observed range {low:.1f}–{high:.1f}.")
    return {
        "baseline": score(base),
        "scenario": result,
        "warnings": bounds,
        "assumptions": "Planning sensitivity, not a causal guarantee. Route and planned timing stay fixed. Historical average matches mode and service only, not load or distance. Classifier probabilities are uncalibrated; review model quality before relying on risk estimates.",
    }
