import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, REAL, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SalesOrders(Base):
    __tablename__ = "sales_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    order_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    promised_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[str] = mapped_column(
        ENUM(name="sales_order_priorities", create_type=False), nullable=False
    )
    status: Mapped[str] = mapped_column(
        ENUM(name="sales_order_statuses", create_type=False), nullable=False
    )
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    total_value_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    assigned_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
