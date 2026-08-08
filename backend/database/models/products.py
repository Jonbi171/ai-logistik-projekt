import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, REAL, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Products(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    sku: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    product_type: Mapped[str] = mapped_column(
        ENUM(name="product_types", create_type=False), nullable=False
    )
    product_family: Mapped[str] = mapped_column(Text, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(Text, nullable=False)
    unit_cost_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    selling_price_sek: Mapped[float] = mapped_column(REAL, nullable=False)
    weight_kg: Mapped[float] = mapped_column(REAL, nullable=False)
    volume_m3: Mapped[float] = mapped_column(REAL, nullable=False)
    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
