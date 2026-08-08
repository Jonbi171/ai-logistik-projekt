import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, REAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ProductSuppliers(Base):
    __tablename__ = "product_suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    supplier_product_code: Mapped[str] = mapped_column(Text, nullable=False)
    unit_cost_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    minimum_order_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    contracted_lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    supplier_capacity_per_day: Mapped[float] = mapped_column(REAL, nullable=False)
    preferred: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
