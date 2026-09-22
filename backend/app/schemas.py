from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class TransportScenario(StrictRequest):
    shipment_id: str
    distance_km: float | None = Field(default=None, gt=0, le=30000)
    total_weight_kg: float | None = Field(default=None, gt=0, le=100000)
    total_volume_m3: float | None = Field(default=None, gt=0, le=1000)
    transport_mode: Literal["ROAD", "AIR", "OCEAN"] | None = None
    service_level: Literal["STANDARD", "EXPRESS"] | None = None
    carrier_id: str | None = None


class InventoryScenario(StrictRequest):
    inventory_id: str
    demand_change: float = Field(default=20, ge=-90, le=300)
    replenishment: float = Field(default=0, ge=0, le=1000000)
    lead_days: int = Field(default=7, ge=1, le=90)
    safety_stock: float = Field(default=0, ge=0, le=1000000)


class Health(BaseModel):
    status: str
    ready: bool
    source: str | None = None
    extracted_at: str | None = None
    models_trained_at: str | None = None
    message: str | None = None
