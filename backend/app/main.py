import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from backend.app.legacy import app as legacy_router
from backend.app.schemas import Health, InventoryScenario, TransportScenario
from backend.services.inventory import scenario
from backend.services.tower import Tower
from backend.services.transport import predict_transport


@asynccontextmanager
async def lifespan(app):
    app.state.tower = None
    app.state.error = None
    try:
        app.state.tower = Tower()
    except Exception as exc:
        logging.getLogger(__name__).error(
            "Control Tower startup unavailable: %s", type(exc).__name__
        )
        app.state.error = "Analytical snapshot unavailable. Check database access and run ./start-demo.sh to prepare models."
    yield


app = FastAPI(
    title="NordicFlow · Intelligent Control Tower",
    version="1.0.0",
    lifespan=lifespan,
    description="Read-only operational analytics, evaluated ML, and planning scenarios over the project’s synthetic PostgreSQL data.",
)


def tower(request: Request) -> Tower:
    service = request.app.state.tower
    if service is None:
        raise HTTPException(503, request.app.state.error)
    return service


@app.get("/health", response_model=Health)
def health(request: Request):
    service = request.app.state.tower
    if service is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "ready": False, "message": request.app.state.error},
        )
    return {
        "status": "ready",
        "ready": True,
        "source": service.source["source"],
        "extracted_at": service.source["extracted_at"],
        "models_trained_at": service.bundle["trained_at"],
    }


@app.get("/tower/overview")
def get_overview(request: Request):
    return tower(request).overview


@app.get("/tower/shipments")
def get_shipments(
    request: Request,
    q: str = "",
    risk: str = "",
    mode: str = "",
    anomalies: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    rows = tower(request).shipments
    if q:
        rows = [
            r
            for r in rows
            if q.casefold()
            in " ".join(
                str(r.get(k, ""))
                for k in ["shipment_number", "carrier", "origin", "destination", "orders"]
            ).casefold()
        ]
    if risk:
        rows = [r for r in rows if r["risk"] == risk]
    if mode:
        rows = [r for r in rows if r["transport_mode"] == mode]
    if anomalies:
        rows = [r for r in rows if r["anomaly"]]
    return {
        "items": rows[offset : offset + limit],
        "total": len(rows),
        "offset": offset,
        "replay": True,
    }


@app.get("/tower/inventory")
def get_inventory(request: Request):
    return {"items": tower(request).inventory}


@app.get("/tower/shipments/{shipment_id}")
def get_shipment(shipment_id: str, request: Request):
    row = next((r for r in tower(request).shipments if r["id"] == shipment_id), None)
    if row is None:
        raise HTTPException(404, "Shipment not found in the held-out replay period")
    return row


@app.get("/tower/demand")
def get_demand(request: Request):
    return {"items": tower(request).forecasts}


@app.get("/tower/suppliers")
def get_suppliers(request: Request):
    return {"items": tower(request).suppliers}


@app.get("/tower/production")
def get_production(request: Request):
    return tower(request).production


@app.get("/tower/models")
def get_models(request: Request):
    return {"items": tower(request).bundle["cards"]}


@app.get("/tower/exceptions")
def get_exceptions(request: Request):
    return {"items": tower(request).exceptions}


@app.get("/tower/options")
def get_options(request: Request):
    service = tower(request)
    org = service.tables["organizations"]
    carriers = org[org.organization_type == "CARRIER"][["id", "name"]].to_dict("records")
    return {"carriers": carriers}


@app.post("/tower/scenarios/transport")
def transport_scenario(body: TransportScenario, request: Request):
    service = tower(request)
    if body.carrier_id is not None and body.carrier_id not in set(
        service.tables["shipments"].carrier_id
    ):
        raise HTTPException(422, "Unknown carrier")
    try:
        return predict_transport(
            service.tables,
            service.bundle,
            body.shipment_id,
            body.model_dump(exclude={"shipment_id"}),
        )
    except KeyError:
        raise HTTPException(404, "Shipment not found") from None


@app.post("/tower/scenarios/inventory")
def inventory_scenario(body: InventoryScenario, request: Request):
    row = next((r for r in tower(request).inventory if r["id"] == body.inventory_id), None)
    if row is None:
        raise HTTPException(404, "Inventory position not found")
    try:
        return scenario(
            row, body.demand_change, body.replenishment, body.lead_days, body.safety_stock
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@app.get("/transport-costs-linreg-prediction")
def legacy_cost_metrics(request: Request):
    return next(c["metrics"] for c in tower(request).bundle["cards"] if c["id"] == "cost")


# Preserve original data exploration endpoints, connecting only when requested.
app.include_router(legacy_router)
