"""Read-only PostgreSQL extraction with an explicit, local offline snapshot."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import text

from backend.database.config import boot

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
TABLES = (
    "shipments",
    "shipment_items",
    "products",
    "locations",
    "organizations",
    "sales_orders",
    "sales_order_lines",
    "inventory_balances",
    "purchase_orders",
    "purchase_order_lines",
    "product_suppliers",
    "transfer_orders",
    "transfer_order_lines",
    "production_orders",
    "production_capacity",
)


def load_data(offline=False):
    path = ARTIFACTS / "snapshot.json"
    if not offline:
        engine = None
        try:
            engine, _ = boot()
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
                    tables = {
                        name: pd.read_sql(text(f"SELECT * FROM public.{name}"), conn)
                        for name in TABLES
                    }
            for frame in tables.values():
                for col in frame.select_dtypes(include=["object", "str"]).columns:
                    frame[col] = frame[col].map(
                        lambda value: str(value) if isinstance(value, UUID) else value
                    )
            ARTIFACTS.mkdir(exist_ok=True)
            payload = {
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "tables": {
                    k: json.loads(v.to_json(orient="records", date_format="iso"))
                    for k, v in tables.items()
                },
            }
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload))
            temp.replace(path)
            return tables, {
                "source": "PostgreSQL",
                "extracted_at": payload["extracted_at"],
                "offline": False,
            }
        except Exception as exc:
            if not path.exists():
                raise RuntimeError(
                    "PostgreSQL unavailable and no snapshot exists. Check DATABASE_URL or database.ini, then run training while connected."
                ) from None
            print(
                f"Using saved PostgreSQL snapshot ({type(exc).__name__}); no generated fallback data."
            )
        finally:
            if engine is not None:
                engine.dispose()
    if not path.exists():
        raise RuntimeError("No local snapshot. Run training with database access first.")
    payload = json.loads(path.read_text())
    return {k: pd.DataFrame(v) for k, v in payload["tables"].items()}, {
        "source": "Saved PostgreSQL snapshot",
        "extracted_at": payload["extracted_at"],
        "offline": True,
    }


def dates(series):
    return pd.to_datetime(series, utc=True, errors="coerce")


def records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


if __name__ == "__main__":
    tables, meta = load_data(os.getenv("DEMO_OFFLINE") == "1")
    print(meta)
    for name, frame in tables.items():
        print(name, len(frame), ",".join(frame.columns))
        for col in ["status", "transport_mode", "service_level", "product_type", "location_type"]:
            if col in frame:
                print(col, frame[col].value_counts().to_dict())
        for col in ["planned_departure_at", "actual_arrival_at", "order_date", "as_of_timestamp"]:
            if col in frame:
                print(
                    col,
                    str(dates(frame[col]).min()),
                    str(dates(frame[col]).max()),
                    "missing",
                    int(frame[col].isna().sum()),
                )
