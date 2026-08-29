"""Reflection registry for the PostgreSQL views managed in Neon."""

from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Engine


VIEW_NAMES = (
    "vw_current_inventory",
    "vw_inventory_movements",
    "vw_product_bom",
    "vw_product_suppliers",
    "vw_purchase_order_lines",
    "vw_sales_order_lines",
    "vw_shipment_events",
    "vw_shipments_overview",
)


def reflect_views(engine: Engine) -> dict[str, Table]:
    """Load the existing public views and their columns from PostgreSQL."""
    metadata = MetaData()
    return {
        name: Table(
            name,
            metadata,
            schema="public",
            autoload_with=engine,
        )
        for name in VIEW_NAMES
    }
