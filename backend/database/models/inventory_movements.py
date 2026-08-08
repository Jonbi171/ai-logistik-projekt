import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class InventoryMovements(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(sales_order_line_id, purchase_order_line_id, "
            "production_order_id, transfer_order_line_id, inventory_adjustment_id) <= 1",
            name="chk_inventory_movement_single_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    movement_type: Mapped[str] = mapped_column(
        ENUM(name="inventory_movement_types", create_type=False), nullable=False
    )
    quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reference_type: Mapped[str] = mapped_column(Text, nullable=False)
    sales_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_order_lines.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    reason_code: Mapped[str] = mapped_column(
        ENUM(name="inventory_movement_reason_codes", create_type=False), nullable=False
    )
    lot_number: Mapped[str] = mapped_column(Text, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    production_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("production_orders.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    transfer_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfer_order_lines.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    inventory_adjustment_id: Mapped[str | None] = mapped_column(Text, nullable=True)
