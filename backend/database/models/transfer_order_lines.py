import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, REAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TransferOrderLines(Base):
    __tablename__ = "transfer_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    transfer_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfer_orders.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    requested_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    shipped_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    received_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
