import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Shipments(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shipment_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    shipment_type: Mapped[str] = mapped_column(
        ENUM(name="shipment_shipment_types", create_type=False), nullable=False
    )
    origin_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    destination_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    carrier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    transport_mode: Mapped[str] = mapped_column(
        ENUM(name="shipment_transport_modes", create_type=False), nullable=False
    )
    service_level: Mapped[str] = mapped_column(
        ENUM(name="shipment_service_levels", create_type=False), nullable=False
    )
    planned_departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_eta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM(name="shipment_statuses", create_type=False), nullable=False
    )
    freight_cost_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    distance_km: Mapped[float] = mapped_column(REAL, nullable=False)
    total_weight_kg: Mapped[float] = mapped_column(REAL, nullable=False)
    total_volume_m3: Mapped[float] = mapped_column(REAL, nullable=False)
    delay_hours: Mapped[float] = mapped_column(REAL, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
