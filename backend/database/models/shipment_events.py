import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ShipmentEvents(Base):
    __tablename__ = "shipment_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    event_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(
        ENUM(name="shipment_events_event_type", create_type=False), nullable=False
    )
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    latitude: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    longitude: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    status_code: Mapped[str] = mapped_column(
        ENUM(name="shipment_events_status_codes", create_type=False), nullable=False
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
