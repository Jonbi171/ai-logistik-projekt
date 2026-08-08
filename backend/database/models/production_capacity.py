import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ProductionCapacity(Base):
    __tablename__ = "production_capacity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    plant_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    capacity_date: Mapped[date] = mapped_column(Date, nullable=False)
    available_hours: Mapped[float] = mapped_column(REAL, nullable=False)
    planned_capacity_units: Mapped[float] = mapped_column(REAL, nullable=False)
    actual_capacity_units: Mapped[float] = mapped_column(REAL, nullable=False)
    downtime_minutes: Mapped[float] = mapped_column(REAL, nullable=False)
    capacity_reason: Mapped[str] = mapped_column(
        ENUM(name="production_capacity_capacity_reasons", create_type=False), nullable=False
    )
    utilization_rate: Mapped[float] = mapped_column(REAL, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
