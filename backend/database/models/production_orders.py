import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ProductionOrders(Base):
    __tablename__ = "production_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    production_order_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    plant_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    planned_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    produced_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    scrapped_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    planned_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM(name="production_order_statuses", create_type=False), nullable=False
    )
    priority: Mapped[str] = mapped_column(
        ENUM(name="production_order_priorities", create_type=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
