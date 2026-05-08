import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

DevicePlatform = sa.Enum("ios", "android", "web", name="device_platform", create_type=False)


class Device(Base):
    __tablename__ = "device"
    # V8: expo_token 글로벌 UNIQUE → (user_id, expo_token) 복합 UNIQUE.
    __table_args__ = (
        UniqueConstraint("user_id", "expo_token", name="uq_device_user_expo_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    expo_token: Mapped[str] = mapped_column(String, nullable=False)
    platform: Mapped[str] = mapped_column(DevicePlatform, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
