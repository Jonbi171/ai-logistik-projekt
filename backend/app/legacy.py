from collections.abc import Generator
from datetime import date
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import String, and_, cast, func, inspect, select, text
from sqlalchemy.orm import Session

import backend.database.models as dbModels
from backend.database.config import boot
from backend.database.views import reflect_views


@lru_cache(maxsize=1)
def legacy_database():
    engine, sessions = boot()
    return engine, sessions


class LazyViews:
    def __getitem__(self, name):
        return legacy_views()[name]


@lru_cache(maxsize=1)
def legacy_views():
    return reflect_views(legacy_database()[0])


views = LazyViews()
app = APIRouter()


def get_session() -> Generator[Session, None, None]:
    with legacy_database()[1]() as session:
        session.execute(text("SET TRANSACTION READ ONLY"))
        yield session


def model_to_dict(instance: Any) -> dict[str, Any]:
    return {
        attribute.key: getattr(instance, attribute.key)
        for attribute in inspect(instance).mapper.column_attrs
    }


def percentage(part: int | float, whole: int | float) -> float:
    return round((part / whole) * 100, 2) if whole else 0.0


def overview_response(
    view_name: str,
    rows: list[dict[str, Any]],
    kpis: dict[str, Any],
    total_records: int,
) -> dict[str, Any]:
    return {
        "view": view_name,
        "summary": {
            "total_records": total_records,
            "returned_records": len(rows),
            **kpis,
        },
        "items": rows,
    }


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/product-suppliers")
def list_product_suppliers(
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    statement = select(dbModels.ProductSuppliers).order_by(dbModels.ProductSuppliers.id)

    product_suppliers = session.scalars(statement).all()

    return [model_to_dict(product_supplier) for product_supplier in product_suppliers]


@app.get("/product-suppliers-order-cost", response_class=PlainTextResponse)
def list_product_suppliers_by_order_cost(
    session: Session = Depends(get_session),
) -> str:
    statement = select(
        dbModels.ProductSuppliers.minimum_order_quantity,
        dbModels.ProductSuppliers.unit_cost_sek,
    )

    rows = session.execute(statement).mappings().all()

    costs = "\n".join(str(row["minimum_order_quantity"] * row["unit_cost_sek"]) for row in rows)

    return f"The product suppliers have the following minimum order costs:\n{costs}"


@app.get("/current-inventory")
def get_current_inventory(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_current_inventory"]
    statement = (
        select(
            view.c.sku,
            view.c.product_name,
            view.c.product_type,
            view.c.unit_of_measure,
            view.c.location_code,
            view.c.location_name,
            view.c.city,
            view.c.on_hand_quantity,
            view.c.reserved_quantity,
            view.c.available_quantity,
            view.c.in_transit_quantity,
            view.c.damaged_quantity,
            view.c.safety_stock_quantity,
            view.c.reorder_point_quantity,
            view.c.quantity_above_safety_stock,
            view.c.inventory_status,
            view.c.as_of_timestamp,
        )
        .order_by(
            view.c.product_name,
            view.c.location_name,
        )
        .limit(limit)
    )

    results = session.execute(statement).mappings().all()
    rows = [
        {
            "product": {
                "sku": row["sku"],
                "name": row["product_name"],
                "type": row["product_type"],
                "unit_of_measure": row["unit_of_measure"],
            },
            "location": {
                "code": row["location_code"],
                "name": row["location_name"],
                "city": row["city"],
            },
            "quantities": {
                "on_hand": row["on_hand_quantity"],
                "reserved": row["reserved_quantity"],
                "available": row["available_quantity"],
                "in_transit": row["in_transit_quantity"],
                "damaged": row["damaged_quantity"],
                "safety_stock": row["safety_stock_quantity"],
                "reorder_point": row["reorder_point_quantity"],
                "above_safety_stock": row["quantity_above_safety_stock"],
            },
            "status": row["inventory_status"],
            "as_of_timestamp": row["as_of_timestamp"],
        }
        for row in results
    ]
    metrics = (
        session.execute(
            select(
                func.count().label("total_records"),
                func.coalesce(func.sum(view.c.on_hand_quantity), 0).label("on_hand"),
                func.coalesce(func.sum(view.c.available_quantity), 0).label("available"),
                func.count().filter(view.c.inventory_status == "STOCKOUT").label("stockouts"),
            )
        )
        .mappings()
        .one()
    )
    statuses = dict(
        session.execute(
            select(view.c.inventory_status, func.count()).group_by(view.c.inventory_status)
        ).all()
    )
    return overview_response(
        "vw_current_inventory",
        rows,
        {
            "inventory_on_hand": metrics["on_hand"],
            "inventory_available": metrics["available"],
            "stockout_locations": metrics["stockouts"],
            "inventory_status_breakdown": statuses,
        },
        metrics["total_records"],
    )


@app.get("/shipment-overview")
def get_shipment_overview(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_shipments_overview"]
    statement = (
        select(
            view.c.shipment_number,
            view.c.shipment_type,
            view.c.transport_mode,
            view.c.service_level,
            view.c.status,
            view.c.origin_location_code,
            view.c.origin_location_name,
            view.c.destination_location_code,
            view.c.destination_location_name,
            view.c.carrier_name,
            view.c.planned_departure_at,
            view.c.actual_departure_at,
            view.c.planned_arrival_at,
            view.c.current_eta,
            view.c.actual_arrival_at,
            view.c.delay_hours,
            view.c.delayed,
            view.c.freight_cost_sek,
            view.c.freight_cost_per_km,
        )
        .order_by(view.c.planned_arrival_at.desc())
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "shipment_number": row["shipment_number"],
            "type": row["shipment_type"],
            "status": row["status"],
            "transport": {
                "mode": row["transport_mode"],
                "service_level": row["service_level"],
                "carrier": row["carrier_name"],
            },
            "route": {
                "origin": {
                    "code": row["origin_location_code"],
                    "name": row["origin_location_name"],
                },
                "destination": {
                    "code": row["destination_location_code"],
                    "name": row["destination_location_name"],
                },
            },
            "schedule": {
                "planned_departure": row["planned_departure_at"],
                "actual_departure": row["actual_departure_at"],
                "planned_arrival": row["planned_arrival_at"],
                "current_eta": row["current_eta"],
                "actual_arrival": row["actual_arrival_at"],
            },
            "delay": {
                "delayed": row["delayed"],
                "hours": row["delay_hours"],
            },
            "cost": {
                "freight_cost_sek": row["freight_cost_sek"],
                "freight_cost_per_km": row["freight_cost_per_km"],
            },
        }
        for row in results
    ]
    metrics = (
        session.execute(
            select(
                func.count().label("total_records"),
                func.count().filter(view.c.delayed.is_(True)).label("delayed"),
                func.coalesce(func.avg(view.c.delay_hours), 0).label("average_delay"),
            )
        )
        .mappings()
        .one()
    )
    return overview_response(
        "vw_shipments_overview",
        rows,
        {
            "delayed_shipments": metrics["delayed"],
            "shipment_delay_rate_percent": percentage(metrics["delayed"], metrics["total_records"]),
            "average_delay_hours": round(float(metrics["average_delay"]), 2),
        },
        metrics["total_records"],
    )


@app.get("/sales-order-overview")
def get_sales_order_overview(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_sales_order_lines"]
    statement = (
        select(
            view.c.sales_order_id,
            view.c.order_number,
            view.c.order_requested_delivery_date,
            view.c.promised_delivery_date,
            view.c.order_priority,
            view.c.order_status,
            view.c.customer_name,
            view.c.warehouse_name,
            view.c.line_number,
            view.c.sku,
            view.c.product_name,
            view.c.ordered_quantity,
            view.c.allocated_quantity,
            view.c.shipped_quantity,
            view.c.delivered_quantity,
            view.c.remaining_quantity,
            view.c.fulfillment_rate,
        )
        .order_by(
            view.c.promised_delivery_date,
            view.c.order_number,
            view.c.line_number,
        )
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "order": {
                "number": row["order_number"],
                "priority": row["order_priority"],
                "status": row["order_status"],
                "requested_delivery_date": row["order_requested_delivery_date"],
                "promised_delivery_date": row["promised_delivery_date"],
                "customer": row["customer_name"],
                "warehouse": row["warehouse_name"],
            },
            "line": {
                "number": row["line_number"],
                "sku": row["sku"],
                "product_name": row["product_name"],
                "ordered": row["ordered_quantity"],
                "allocated": row["allocated_quantity"],
                "shipped": row["shipped_quantity"],
                "delivered": row["delivered_quantity"],
                "remaining": row["remaining_quantity"],
                "fulfillment_rate_percent": round(
                    float(row["fulfillment_rate"]) * 100,
                    2,
                ),
            },
        }
        for row in results
    ]
    late_condition = and_(
        view.c.promised_delivery_date < date.today(),
        view.c.remaining_quantity > 0,
    )
    metrics = (
        session.execute(
            select(
                func.count(func.distinct(view.c.sales_order_id)).label("total_orders"),
                func.coalesce(func.sum(view.c.ordered_quantity), 0).label("ordered"),
                func.coalesce(func.sum(view.c.delivered_quantity), 0).label("delivered"),
                func.count(func.distinct(view.c.sales_order_id))
                .filter(late_condition)
                .label("late_orders"),
                func.count().label("total_records"),
            )
        )
        .mappings()
        .one()
    )
    return overview_response(
        "vw_sales_order_lines",
        rows,
        {
            "total_orders": metrics["total_orders"],
            "order_fulfillment_rate_percent": percentage(metrics["delivered"], metrics["ordered"]),
            "late_orders": metrics["late_orders"],
            "late_order_rate_percent": percentage(metrics["late_orders"], metrics["total_orders"]),
        },
        metrics["total_records"],
    )


@app.get("/purchase-order-overview")
def get_purchase_order_overview(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_purchase_order_lines"]
    statement = (
        select(
            view.c.purchase_order_id,
            view.c.purchase_order_number,
            view.c.order_date,
            view.c.confirmed_delivery_date,
            view.c.actual_delivery_date,
            view.c.purchase_order_status,
            view.c.supplier_name,
            view.c.supplier_country_code,
            view.c.supplier_risk_tier,
            view.c.destination_location_name,
            view.c.line_number,
            view.c.sku,
            view.c.product_name,
            view.c.ordered_quantity,
            view.c.received_quantity,
            view.c.rejected_quantity,
            view.c.outstanding_quantity,
            view.c.purchase_order_line_status,
            view.c.actual_lead_time_days,
            view.c.delivery_date_variance_days,
            view.c.supplier_on_time,
        )
        .order_by(
            view.c.actual_delivery_date.desc(),
            view.c.purchase_order_number,
            view.c.line_number,
        )
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "purchase_order": {
                "number": row["purchase_order_number"],
                "status": row["purchase_order_status"],
                "order_date": row["order_date"],
                "confirmed_delivery_date": row["confirmed_delivery_date"],
                "actual_delivery_date": row["actual_delivery_date"],
                "actual_lead_time_days": row["actual_lead_time_days"],
                "delivery_variance_days": row["delivery_date_variance_days"],
                "supplier_on_time": row["supplier_on_time"],
            },
            "supplier": {
                "name": row["supplier_name"],
                "country_code": row["supplier_country_code"],
                "risk_tier": row["supplier_risk_tier"],
            },
            "destination": row["destination_location_name"],
            "line": {
                "number": row["line_number"],
                "sku": row["sku"],
                "product_name": row["product_name"],
                "status": row["purchase_order_line_status"],
                "ordered": row["ordered_quantity"],
                "received": row["received_quantity"],
                "rejected": row["rejected_quantity"],
                "outstanding": row["outstanding_quantity"],
            },
        }
        for row in results
    ]
    order_metrics = (
        select(
            view.c.purchase_order_id,
            view.c.supplier_on_time,
            view.c.actual_lead_time_days,
        )
        .distinct()
        .subquery()
    )
    metrics = (
        session.execute(
            select(
                func.count().label("total_orders"),
                func.count().filter(order_metrics.c.supplier_on_time.is_(True)).label("on_time"),
                func.coalesce(func.avg(order_metrics.c.actual_lead_time_days), 0).label(
                    "average_lead_time"
                ),
            ).select_from(order_metrics)
        )
        .mappings()
        .one()
    )
    total_records = session.scalar(select(func.count()).select_from(view)) or 0
    return overview_response(
        "vw_purchase_order_lines",
        rows,
        {
            "total_purchase_orders": metrics["total_orders"],
            "average_supplier_lead_time_days": round(float(metrics["average_lead_time"]), 2),
            "on_time_deliveries": metrics["on_time"],
            "on_time_delivery_rate_percent": percentage(
                metrics["on_time"], metrics["total_orders"]
            ),
        },
        total_records,
    )


@app.get("/inventory-history")
def get_inventory_history(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_inventory_movements"]
    statement = (
        select(
            view.c.event_timestamp,
            view.c.movement_type,
            view.c.quantity,
            view.c.reason_code,
            view.c.sku,
            view.c.product_name,
            view.c.unit_of_measure,
            view.c.location_code,
            view.c.location_name,
            view.c.linked_document_type,
            view.c.lot_number,
            view.c.expiry_date,
        )
        .order_by(view.c.event_timestamp.desc())
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "event_timestamp": row["event_timestamp"],
            "movement": {
                "type": row["movement_type"],
                "quantity": row["quantity"],
                "reason": row["reason_code"],
                "linked_document_type": row["linked_document_type"],
            },
            "product": {
                "sku": row["sku"],
                "name": row["product_name"],
                "unit_of_measure": row["unit_of_measure"],
                "lot_number": row["lot_number"],
                "expiry_date": row["expiry_date"],
            },
            "location": {
                "code": row["location_code"],
                "name": row["location_name"],
            },
        }
        for row in results
    ]
    stockout_condition = cast(view.c.reason_code, String).ilike("%STOCKOUT%")
    metrics = (
        session.execute(
            select(
                func.count().label("total_records"),
                func.count().filter(stockout_condition).label("stockout_events"),
            )
        )
        .mappings()
        .one()
    )
    movement_types = dict(
        session.execute(
            select(view.c.movement_type, func.count()).group_by(view.c.movement_type)
        ).all()
    )
    return overview_response(
        "vw_inventory_movements",
        rows,
        {
            "movement_type_breakdown": movement_types,
            "stockout_related_movements": metrics["stockout_events"],
            "stockout_frequency_percent": percentage(
                metrics["stockout_events"], metrics["total_records"]
            ),
            "stockout_frequency_definition": (
                "Movements whose reason code contains STOCKOUT divided by all movements"
            ),
        },
        metrics["total_records"],
    )


@app.get("/product-bom")
def get_product_bom(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_product_bom"]
    statement = (
        select(
            view.c.bom_version,
            view.c.finished_product_sku,
            view.c.finished_product_name,
            view.c.component_product_sku,
            view.c.component_product_name,
            view.c.component_unit_of_measure,
            view.c.quantity_required,
            view.c.scrap_factor,
            view.c.quantity_required_including_scrap,
            view.c.effective_from,
            view.c.effective_to,
        )
        .order_by(
            view.c.finished_product_name,
            view.c.component_product_name,
        )
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "bom_version": row["bom_version"],
            "finished_product": {
                "sku": row["finished_product_sku"],
                "name": row["finished_product_name"],
            },
            "component": {
                "sku": row["component_product_sku"],
                "name": row["component_product_name"],
                "unit_of_measure": row["component_unit_of_measure"],
            },
            "material_requirement": {
                "quantity": row["quantity_required"],
                "scrap_factor_percent": round(float(row["scrap_factor"]) * 100, 2),
                "quantity_including_scrap": row["quantity_required_including_scrap"],
            },
            "effective_period": {
                "from": row["effective_from"],
                "to": row["effective_to"],
            },
        }
        for row in results
    ]
    metrics = (
        session.execute(
            select(
                func.count().label("total_records"),
                func.count(func.distinct(view.c.finished_product_sku)).label("finished_products"),
                func.count().filter(view.c.scrap_factor > 0).label("scrap_lines"),
                func.count().filter(view.c.effective_to < date.today()).label("expired_lines"),
            )
        )
        .mappings()
        .one()
    )
    return overview_response(
        "vw_product_bom",
        rows,
        {
            "finished_products": metrics["finished_products"],
            "component_relationships": metrics["total_records"],
            "relationships_with_scrap": metrics["scrap_lines"],
            "expired_relationships": metrics["expired_lines"],
        },
        metrics["total_records"],
    )


@app.get("/product-supplier-overview")
def get_product_supplier_overview(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_product_suppliers"]
    statement = (
        select(
            view.c.sku,
            view.c.product_name,
            view.c.supplier_name,
            view.c.supplier_country_code,
            view.c.risk_tier,
            view.c.supplier_product_code,
            view.c.unit_cost_sek,
            view.c.minimum_order_quantity,
            view.c.contracted_lead_time_days,
            view.c.supplier_capacity_per_day,
            view.c.preferred,
            view.c.valid_from,
            view.c.valid_to,
        )
        .order_by(
            view.c.product_name,
            view.c.preferred.desc(),
            view.c.supplier_name,
        )
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "product": {
                "sku": row["sku"],
                "name": row["product_name"],
            },
            "supplier": {
                "name": row["supplier_name"],
                "country_code": row["supplier_country_code"],
                "risk_tier": row["risk_tier"],
                "product_code": row["supplier_product_code"],
                "preferred": bool(row["preferred"]),
            },
            "commercial_terms": {
                "unit_cost_sek": row["unit_cost_sek"],
                "minimum_order_quantity": row["minimum_order_quantity"],
                "minimum_order_cost_sek": round(
                    float(row["unit_cost_sek"]) * float(row["minimum_order_quantity"]),
                    2,
                ),
                "lead_time_days": row["contracted_lead_time_days"],
                "capacity_per_day": row["supplier_capacity_per_day"],
            },
            "validity": {
                "from": row["valid_from"],
                "to": row["valid_to"],
            },
        }
        for row in results
    ]
    metrics = (
        session.execute(
            select(
                func.count().label("total_records"),
                func.count().filter(view.c.preferred != 0).label("preferred"),
                func.coalesce(func.avg(view.c.contracted_lead_time_days), 0).label(
                    "average_lead_time"
                ),
            )
        )
        .mappings()
        .one()
    )
    risk_tiers = dict(
        session.execute(select(view.c.risk_tier, func.count()).group_by(view.c.risk_tier)).all()
    )
    return overview_response(
        "vw_product_suppliers",
        rows,
        {
            "preferred_supplier_rate_percent": percentage(
                metrics["preferred"], metrics["total_records"]
            ),
            "average_contracted_lead_time_days": round(float(metrics["average_lead_time"]), 2),
            "supplier_risk_tier_breakdown": risk_tiers,
        },
        metrics["total_records"],
    )


@app.get("/shipment-events")
def get_shipment_events(
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    view = views["vw_shipment_events"]
    statement = (
        select(
            view.c.shipment_id,
            view.c.shipment_number,
            view.c.event_sequence,
            view.c.event_type,
            view.c.event_timestamp,
            view.c.status_code,
            view.c.source,
            view.c.location_code,
            view.c.location_name,
            view.c.city,
            view.c.country_code,
        )
        .order_by(view.c.event_timestamp.desc(), view.c.shipment_number)
        .limit(limit)
    )
    results = session.execute(statement).mappings().all()
    rows = [
        {
            "shipment_number": row["shipment_number"],
            "event": {
                "sequence": row["event_sequence"],
                "type": row["event_type"],
                "status_code": row["status_code"],
                "timestamp": row["event_timestamp"],
                "source": row["source"],
            },
            "location": {
                "code": row["location_code"],
                "name": row["location_name"],
                "city": row["city"],
                "country_code": row["country_code"],
            },
        }
        for row in results
    ]
    metrics = (
        session.execute(
            select(
                func.count().label("total_records"),
                func.count(func.distinct(view.c.shipment_id)).label("shipments"),
                func.max(view.c.event_timestamp).label("latest_event"),
            )
        )
        .mappings()
        .one()
    )
    event_types = dict(
        session.execute(select(view.c.event_type, func.count()).group_by(view.c.event_type)).all()
    )
    return overview_response(
        "vw_shipment_events",
        rows,
        {
            "shipments_tracked": metrics["shipments"],
            "event_type_breakdown": event_types,
            "latest_event_timestamp": metrics["latest_event"],
        },
        metrics["total_records"],
    )
