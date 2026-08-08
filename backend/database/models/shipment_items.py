import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ShipmentItems(Base):
    __tablename__ = "shipment_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    sales_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_order_lines.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    purchase_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    transfer_order_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfer_order_lines.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=True
    )
    source_document_type: Mapped[str] = mapped_column(
        ENUM(name="shipment_items_source_document_types", create_type=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
