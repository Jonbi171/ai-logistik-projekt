"""Weekly demand forecasting, zero-filled calendar and chronological holdout."""

import numpy as np
import pandas as pd

from backend.services.data import dates


def estimate(values, method):
    x = np.asarray(values, dtype=float)
    if method == "Last week":
        return float(x[-1])
    if method == "4-week moving average":
        return float(np.mean(x[-4:]))
    level = x[0]
    for value in x[1:]:
        level = 0.3 * value + 0.7 * level
    return float(level)


def metrics(actual, predicted):
    a, p = np.asarray(actual), np.asarray(predicted)
    return {
        "mae": float(np.mean(abs(p - a))),
        "rmse": float(np.sqrt(np.mean((p - a) ** 2))),
        "wape": float(sum(abs(p - a)) / sum(abs(a))) if sum(abs(a)) else None,
        "bias": float(np.mean(p - a)),
        "mape": float(np.mean(abs((p[a != 0] - a[a != 0]) / a[a != 0])))
        if np.any(a != 0)
        else None,
    }


def build_forecasts(tables):
    orders = tables["sales_orders"]
    orders = orders[~orders.status.isin(["CANCELLED", "CANCELED"])]
    lines = tables["sales_order_lines"].merge(
        orders[["id", "order_date", "assigned_warehouse_id"]],
        left_on="sales_order_id",
        right_on="id",
        suffixes=("", "_order"),
    )
    lines["day"] = dates(lines.order_date).dt.tz_localize(None)
    lines["week"] = lines.day.dt.to_period("W-SUN").dt.start_time
    start, end = lines.week.min(), lines.week.max()
    # Drop the newest partial week; forecasts start at that week's boundary.
    calendar = pd.date_range(start, end - pd.Timedelta(weeks=1), freq="W-MON")
    if len(calendar) < 16:
        raise ValueError("At least 16 completed weeks are needed for forecasting.")
    forecasts = []
    for product_id, group in lines.groupby("product_id"):
        weekly = group.groupby("week").ordered_quantity.sum().reindex(calendar, fill_value=0)
        values = weekly.to_numpy(float)
        train, holdout = values[:-8], values[-8:]
        methods = ["Last week", "4-week moving average", "Exponential smoothing (α=0.3)"]
        # Select on an inner chronological validation window, never on reported test data.
        scores = {m: sum(abs(train[-4:] - estimate(train[:-4], m))) for m in methods}
        method = min(scores, key=scores.get)
        prediction = np.repeat(estimate(train, method), 8)
        performance = metrics(holdout, prediction)
        baseline = metrics(holdout, np.repeat(estimate(train, "4-week moving average"), 8))
        residuals = [
            values[i] - estimate(values[:i], method)
            for i in range(max(4, len(values) - 20), len(values))
        ]
        sigma = float(np.std(residuals))
        level = max(0, estimate(values, method))
        product = tables["products"].set_index("id").loc[product_id]
        future = []
        for i in range(4):
            future.append(
                {
                    "week": str((end + pd.Timedelta(weeks=i)).date()),
                    "forecast": round(level, 2),
                    "lower": round(max(0, level - 1.28 * sigma), 2),
                    "upper": round(level + 1.28 * sigma, 2),
                }
            )
        history = [
            {
                "week": str(day.date()),
                "actual": round(float(value), 2),
                "backtest": round(float(prediction[j - (len(values) - 8)]), 2)
                if j >= len(values) - 8
                else None,
            }
            for j, (day, value) in enumerate(weekly.items())
        ]
        recent = group[group.week >= calendar[-12]]
        location_demand = recent.groupby("assigned_warehouse_id").ordered_quantity.sum()
        total = float(location_demand.sum())
        forecasts.append(
            {
                "product_id": str(product_id),
                "sku": product.sku,
                "product": product["name"],
                "unit": product.unit_of_measure,
                "model": method,
                "weeks": len(values),
                "next_4_weeks": round(level * 4, 2),
                "weekly": level,
                "sigma": sigma,
                "metrics": performance,
                "baseline": baseline,
                "history": history,
                "future": future,
                "location_shares": {str(k): float(v / total) for k, v in location_demand.items()}
                if total
                else {},
                "methodology": "Weekly ordered demand; cancelled orders excluded; missing weeks zero-filled; newest partial week excluded. Model selected on inner 4-week validation, evaluated on untouched final 8 weeks. Forecast band is an approximate 80% residual range, not a calibrated service guarantee.",
            }
        )
    return forecasts
