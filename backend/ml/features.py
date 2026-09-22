"""Prediction-time features only; outcomes are kept outside these builders."""

from backend.services.data import dates

SHIP_NUM = [
    "total_weight_kg",
    "total_volume_m3",
    "distance_km",
    "planned_transit_hours",
    "weekday",
    "month",
]
SHIP_CAT = [
    "transport_mode",
    "service_level",
    "carrier_id",
    "origin_location_id",
    "destination_location_id",
]
COST_NUM = ["total_weight_kg", "total_volume_m3", "distance_km"]
COST_CAT = ["transport_mode", "service_level", "carrier_id"]
SUP_NUM = ["total_value_sek", "planned_lead_days", "weekday", "month"]
SUP_CAT = ["supplier_id", "destination_location_id"]


def shipment_features(frame):
    result = frame.copy()
    departure = dates(result["planned_departure_at"])
    result["planned_transit_hours"] = (
        dates(result["planned_arrival_at"]) - departure
    ).dt.total_seconds() / 3600
    result["weekday"] = departure.dt.dayofweek
    result["month"] = departure.dt.month
    for c in SHIP_CAT:
        result[c] = result[c].fillna("Unknown").astype(str)
    return result[SHIP_NUM + SHIP_CAT]


def supplier_features(frame):
    result = frame.copy()
    day = dates(result["order_date"])
    # Requested delivery is known at placement; final confirmations may be revised later.
    result["planned_lead_days"] = (dates(result["requested_delivery_date"]) - day).dt.days
    result["weekday"] = day.dt.dayofweek
    result["month"] = day.dt.month
    for c in SUP_CAT:
        result[c] = result[c].fillna("Unknown").astype(str)
    return result[SUP_NUM + SUP_CAT]


def temporal_split(frame, event_col, outcome_col):
    """Latest 20% dates hold out; purge labels not observable at the cutoff."""
    ordered = frame.sort_values(event_col).reset_index(drop=True)
    cutoff = dates(ordered[event_col]).quantile(0.8)
    train = ordered[(dates(ordered[event_col]) < cutoff) & (dates(ordered[outcome_col]) < cutoff)]
    test = ordered[dates(ordered[event_col]) >= cutoff]
    if len(train) < 40 or len(test) < 10:
        raise ValueError("Insufficient chronological history for an honest train/test evaluation.")
    return train.copy(), test.copy(), cutoff
