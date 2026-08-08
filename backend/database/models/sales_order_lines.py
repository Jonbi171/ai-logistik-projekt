import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SalesOrderLines(Base):
    __tablename__ = "sales_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    sales_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_orders.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    ordered_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    allocated_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    shipped_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    delivered_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    unit_price_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    requested_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM(name="sales_order_line_statuses", create_type=False), nullable=False
    )
    created_at: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[date] = mapped_column(Date, nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
