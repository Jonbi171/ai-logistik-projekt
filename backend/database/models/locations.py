import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, REAL, String, Text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Locations(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    location_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    location_type: Mapped[str] = mapped_column(
        ENUM(name="location_types", create_type=False), nullable=False
    )
    country_code: Mapped[str] = mapped_column(String(3), nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    longitude: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False)
    storage_capacity: Mapped[float] = mapped_column(REAL, nullable=False)
    daily_handling_capacity: Mapped[float] = mapped_column(REAL, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
