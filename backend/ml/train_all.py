"""Run once (or explicitly retrain): python -m backend.ml.train_all [--offline]."""

import argparse
import json
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.ml.features import (
    COST_CAT,
    COST_NUM,
    SHIP_CAT,
    SHIP_NUM,
    SUP_CAT,
    SUP_NUM,
    shipment_features,
    supplier_features,
    temporal_split,
)
from backend.ml.forecast import build_forecasts
from backend.services.data import ARTIFACTS, dates, load_data

VERSION = 1


def pipeline(model, nums, cats):
    return Pipeline(
        [
            (
                "preprocess",
                ColumnTransformer(
                    [
                        (
                            "numeric",
                            Pipeline(
                                [
                                    ("impute", SimpleImputer(strategy="median")),
                                    ("scale", StandardScaler()),
                                ]
                            ),
                            nums,
                        ),
                        (
                            "categorical",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                            cats,
                        ),
                    ]
                ),
            ),
            ("model", model),
        ]
    )


def classification(y, probabilities):
    predicted = probabilities >= 0.5
    return {
        "accuracy": accuracy_score(y, predicted),
        "precision": precision_score(y, predicted, zero_division=0),
        "recall": recall_score(y, predicted, zero_division=0),
        "f1": f1_score(y, predicted, zero_division=0),
        "roc_auc": roc_auc_score(y, probabilities) if len(np.unique(y)) > 1 else None,
        "brier_score": brier_score_loss(y, probabilities),
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
    }


def regression(y, predicted):
    return {
        "mae": mean_absolute_error(y, predicted),
        "rmse": float(np.sqrt(mean_squared_error(y, predicted))),
        "r2": r2_score(y, predicted),
    }


def importance(model):
    estimator = model.named_steps["model"]
    names = model.named_steps["preprocess"].get_feature_names_out()
    weights = getattr(estimator, "feature_importances_", None)
    if weights is None:
        weights = np.abs(estimator.coef_).reshape(-1)
    result = sorted(zip(names, weights), key=lambda pair: pair[1], reverse=True)[:10]
    return [
        {
            "feature": str(k).replace("numeric__", "").replace("categorical__", ""),
            "importance": float(v),
        }
        for k, v in result
    ]


def train(offline=False):
    tables, source = load_data(offline)
    trained_at = datetime.now(timezone.utc).isoformat()
    models, cards = {}, []
    raw = tables["shipments"]
    valid = (
        dates(raw.actual_arrival_at).notna()
        & dates(raw.planned_arrival_at).notna()
        & dates(raw.planned_departure_at).notna()
        & ~raw.status.isin(["CANCELLED", "CANCELED"])
    )
    shipments = raw[valid].copy()
    shipments["target_delay"] = (
        (
            dates(shipments.actual_arrival_at) - dates(shipments.planned_arrival_at)
        ).dt.total_seconds()
        / 3600
    ).clip(lower=0)
    shipments["target_late"] = (shipments.target_delay > 0).astype(int)
    train_set, test_set, cutoff = temporal_split(
        shipments, "planned_departure_at", "actual_arrival_at"
    )
    Xtr, Xte = shipment_features(train_set), shipment_features(test_set)
    if train_set.target_late.nunique() < 2:
        raise ValueError(
            "Shipment history has only one outcome class; cannot train a delay classifier."
        )
    specs = [
        (
            "delay",
            "Shipment delay risk",
            RandomForestClassifier(
                n_estimators=140, max_depth=10, min_samples_leaf=12, random_state=42, n_jobs=-1
            ),
            LogisticRegression(max_iter=1200),
            "target_late",
            SHIP_NUM,
            SHIP_CAT,
            "Predict lateness before departure to review delivery commitments.",
            "Random forest captures route and service interactions; compared with logistic regression.",
        ),
        (
            "eta",
            "Delay / ETA",
            RandomForestRegressor(
                n_estimators=120, max_depth=10, min_samples_leaf=12, random_state=42, n_jobs=-1
            ),
            None,
            "target_delay",
            SHIP_NUM,
            SHIP_CAT,
            "Estimate positive delay hours beyond planned arrival.",
            "Random forest handles nonlinear delay patterns without external dependencies.",
        ),
        (
            "cost",
            "Freight cost",
            LinearRegression(),
            RandomForestRegressor(n_estimators=100, min_samples_leaf=8, random_state=42, n_jobs=-1),
            "freight_cost_sek",
            COST_NUM,
            COST_CAT,
            "Estimate transport spend and compare planning scenarios.",
            "Linear regression retains the existing explainable cost-model direction; tree comparison is reported.",
        ),
    ]
    for key, title, estimator, baseline, target, nums, cats, purpose, reason in specs:
        model = pipeline(estimator, nums, cats).fit(Xtr, train_set[target])
        pred = (
            model.predict_proba(Xte)[:, 1] if key == "delay" else np.maximum(0, model.predict(Xte))
        )
        score = (
            classification(test_set[target], pred)
            if key == "delay"
            else regression(test_set[target], pred)
        )
        comparison = None
        if baseline is not None:
            bm = pipeline(baseline, nums, cats).fit(Xtr, train_set[target])
            bp = bm.predict_proba(Xte)[:, 1] if key == "delay" else np.maximum(0, bm.predict(Xte))
            comparison = {
                "model": type(baseline).__name__,
                "metrics": classification(test_set[target], bp)
                if key == "delay"
                else regression(test_set[target], bp),
            }
        # Serving uses the evaluated model unchanged; historical rows are explicitly replay.
        models[key] = model
        cards.append(
            {
                "id": key,
                "name": title,
                "model": type(estimator).__name__,
                "purpose": purpose,
                "target": target,
                "features": nums + cats,
                "observations": len(shipments),
                "train_rows": len(train_set),
                "test_rows": len(test_set),
                "cutoff": cutoff.isoformat(),
                "metrics": score,
                "comparison": comparison,
                "importance": importance(model),
                "reason": reason,
                "validation": "Chronological 80/20 split by planned departure; training outcomes after cutoff purged. Serving retains this evaluated model.",
                "samples": [
                    {"actual": float(a), "predicted": float(p)}
                    for a, p in zip(test_set[target].iloc[:60], pred[:60])
                ],
            }
        )
        print(title, score, flush=True)
    purchase = tables["purchase_orders"].copy()
    purchase = purchase[
        dates(purchase.actual_delivery_date).notna()
        & ~purchase.status.isin(["CANCELLED", "CANCELED"])
    ]
    purchase["target_late"] = (
        dates(purchase.actual_delivery_date) > dates(purchase.requested_delivery_date)
    ).astype(int)
    tr, te, cutoff = temporal_split(purchase, "order_date", "actual_delivery_date")
    if tr.target_late.nunique() > 1:
        supplier_model = pipeline(LogisticRegression(max_iter=1200), SUP_NUM, SUP_CAT).fit(
            supplier_features(tr), tr.target_late
        )
        models["supplier"] = supplier_model
        cards.append(
            {
                "id": "supplier",
                "name": "Supplier delivery risk",
                "model": "LogisticRegression",
                "purpose": "Flag purchase orders likely to miss the originally requested date.",
                "target": "actual_delivery_date > requested_delivery_date",
                "features": SUP_NUM + SUP_CAT,
                "observations": len(purchase),
                "train_rows": len(tr),
                "test_rows": len(te),
                "cutoff": cutoff.isoformat(),
                "metrics": classification(
                    te.target_late, supplier_model.predict_proba(supplier_features(te))[:, 1]
                ),
                "comparison": None,
                "importance": importance(supplier_model),
                "reason": "An interpretable baseline for the smaller purchase-order dataset.",
                "validation": "Chronological split by order date; only outcomes available before cutoff train the model. Final confirmed dates are not features.",
            }
        )
    anom_cols = [
        "freight_cost_sek",
        "distance_km",
        "total_weight_kg",
        "total_volume_m3",
        "target_delay",
    ]
    anom = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            (
                "model",
                IsolationForest(n_estimators=120, contamination=0.04, random_state=42, n_jobs=-1),
            ),
        ]
    ).fit(train_set[anom_cols])
    models["anomaly"] = anom
    cards.append(
        {
            "id": "anomaly",
            "name": "Operational anomalies",
            "model": "IsolationForest",
            "purpose": "Prioritize unusual completed shipments for investigation; unusual does not mean incorrect.",
            "target": "Unsupervised isolation score",
            "features": anom_cols,
            "observations": len(shipments),
            "train_rows": len(train_set),
            "test_rows": len(test_set),
            "metrics": {
                "holdout_flag_rate": float(np.mean(anom.predict(test_set[anom_cols]) == -1))
            },
            "comparison": None,
            "importance": [],
            "reason": "Detects unusual combinations of cost, load, distance and realized delay.",
            "validation": "Fits historical training period; reports flagged share on chronological holdout. Contamination 4% is a sensitivity setting, not measured accuracy.",
        }
    )
    forecasts = build_forecasts(tables)
    total_error = sum(f["metrics"]["mae"] * 8 for f in forecasts)
    total_demand = sum(sum(h["actual"] for h in f["history"][-8:]) for f in forecasts)
    cards.append(
        {
            "id": "demand",
            "name": "SKU demand forecast",
            "model": "Validated statistical baselines",
            "purpose": "Translate sales demand into a four-week supply requirement.",
            "target": "Weekly ordered units by SKU",
            "features": ["order_date", "ordered_quantity", "product_id"],
            "observations": len(tables["sales_order_lines"]),
            "train_rows": sum(f["weeks"] - 8 for f in forecasts),
            "test_rows": 8 * len(forecasts),
            "metrics": {"wape": total_error / total_demand if total_demand else None},
            "comparison": None,
            "importance": [],
            "reason": "Last value, moving average and exponential smoothing are credible benchmarks for this history.",
            "validation": "Inner four-week model selection; final eight complete weeks are an untouched fixed-origin test, then refit for future forecasts.",
        }
    )
    for card in cards:
        card["trained_at"] = trained_at
    bundle = {
        "version": VERSION,
        "trained_at": trained_at,
        "source": source,
        "models": models,
        "cards": cards,
        "forecasts": forecasts,
    }
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / "models.joblib"
    joblib.dump(bundle, path.with_suffix(".tmp"))
    path.with_suffix(".tmp").replace(path)
    (ARTIFACTS / "metrics.json").write_text(json.dumps(cards, indent=2, default=float))
    print(f"Saved {len(models)} model pipelines and {len(forecasts)} SKU forecasts.", flush=True)
    return bundle


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline", action="store_true", help="Train from the saved PostgreSQL snapshot."
    )
    args = parser.parse_args()
    train(args.offline)
