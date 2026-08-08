import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ProductionMaterialConsumption(Base):
    __tablename__ = "production_material_consumption"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    production_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_orders.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    component_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    planned_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    actual_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(Text, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
