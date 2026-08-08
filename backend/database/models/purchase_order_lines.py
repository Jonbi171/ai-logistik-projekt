import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PurchaseOrderLines(Base):
    __tablename__ = "purchase_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    ordered_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    confirmed_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    received_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    rejected_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    unit_cost_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM(name="purchase_order_line_statuses", create_type=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
