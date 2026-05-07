"""0004_diagnosis_event

W3-v2 head-start — `diagnosis_event` 테이블 + modality/action enum.
이미지/오디오 진단 결과를 영구 보관, `/v1/pets/{id}/diagnoses` 조회 대상.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-07
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    sa.Enum("image", "audio", "timeseries", name="diagnosis_modality").create(
        op.get_bind(), checkfirst=True
    )
    sa.Enum("immediate", "schedule", "observe", name="diagnosis_action").create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "diagnosis_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "pet_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pet.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "modality",
            sa.Enum(
                "image",
                "audio",
                "timeseries",
                name="diagnosis_modality",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("s3_ref", sa.String(), nullable=False),
        sa.Column("top_results", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "action",
            sa.Enum(
                "immediate",
                "schedule",
                "observe",
                name="diagnosis_action",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("confidence_top1", sa.Double(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_diagnosis_event_pet_created",
        "diagnosis_event",
        ["pet_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_diagnosis_event_pet_created", table_name="diagnosis_event")
    op.drop_table("diagnosis_event")
    op.execute("DROP TYPE IF EXISTS diagnosis_action")
    op.execute("DROP TYPE IF EXISTS diagnosis_modality")
