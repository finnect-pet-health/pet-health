import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

DiagnosisModality = sa.Enum(
    "image", "audio", "timeseries", name="diagnosis_modality", create_type=False
)
DiagnosisAction = sa.Enum(
    "immediate", "schedule", "observe", name="diagnosis_action", create_type=False
)


class DiagnosisEvent(Base):
    __tablename__ = "diagnosis_event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pet.id", ondelete="CASCADE"), nullable=False
    )
    modality: Mapped[str] = mapped_column(DiagnosisModality, nullable=False)
    s3_ref: Mapped[str] = mapped_column(String, nullable=False)
    top_results: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    action: Mapped[str] = mapped_column(DiagnosisAction, nullable=False)
    confidence_top1: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
