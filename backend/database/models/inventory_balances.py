import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, REAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class InventoryBalances(Base):
    __tablename__ = "inventory_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    on_hand_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    reserved_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    available_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    in_transit_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    damaged_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    safety_stock_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    reorder_point_quantity: Mapped[float] = mapped_column(REAL, nullable=False)
    as_of_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
