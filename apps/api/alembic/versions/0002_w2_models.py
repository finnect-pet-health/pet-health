"""0002_w2_models

W2-v2 Day 1 — 6 new tables (meal, calendar_task, vet_visit, pet_food, notification_log, device).

NOTE: Pet table ALTER (memo, allergies, photo_url, deleted_at columns) is intentionally
deferred to 5.8 D2 morning to preserve W1 freeze. This migration creates new tables only.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- create enums ---
    sa.Enum("fatsecret", "custom", "seed", name="meal_source").create(
        op.get_bind(), checkfirst=True
    )
    sa.Enum("사료", "간식", "일반식", "처방식", name="meal_food_kind").create(
        op.get_bind(), checkfirst=True
    )
    sa.Enum(
        "meal", "walk", "medicine", "vet", "custom", name="calendar_task_kind"
    ).create(op.get_bind(), checkfirst=True)
    sa.Enum("seed", "fatsecret", "user", name="pet_food_source").create(
        op.get_bind(), checkfirst=True
    )
    sa.Enum("expo", "log", name="notification_channel").create(
        op.get_bind(), checkfirst=True
    )
    sa.Enum("ios", "android", "web", name="device_platform").create(
        op.get_bind(), checkfirst=True
    )

    # --- meal ---
    op.create_table(
        "meal",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "pet_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pet.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source",
            sa.Enum("fatsecret", "custom", "seed", name="meal_source", create_type=False),
            nullable=False,
        ),
        sa.Column("food_id", sa.String(), nullable=True),
        sa.Column("food_name", sa.String(), nullable=False),
        sa.Column("qty_g", sa.Double(), nullable=False),
        sa.Column("kcal", sa.Double(), nullable=True),
        sa.Column("protein_g", sa.Double(), nullable=True),
        sa.Column("carbs_g", sa.Double(), nullable=True),
        sa.Column("fat_g", sa.Double(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column(
            "food_kind",
            sa.Enum("사료", "간식", "일반식", "처방식", name="meal_food_kind", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_meal_pet_ts", "meal", ["pet_id", "ts"])

    # --- calendar_task ---
    op.create_table(
        "calendar_task",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "family_id",
            UUID(as_uuid=True),
            sa.ForeignKey("family.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pet_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pet.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "meal", "walk", "medicine", "vet", "custom",
                name="calendar_task_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "assignee_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_calendar_task_family_due", "calendar_task", ["family_id", "due_at"])
    op.create_index(
        "ix_calendar_task_assignee",
        "calendar_task",
        ["assignee_id"],
        postgresql_where=sa.text("assignee_id IS NOT NULL"),
    )

    # --- vet_visit ---
    op.create_table(
        "vet_visit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "pet_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pet.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("visited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hospital_name", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("cost_krw", sa.Integer(), nullable=True),
        sa.Column(
            "attachments",
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_vet_visit_pet_visited",
        "vet_visit",
        ["pet_id", sa.text("visited_at DESC")],
    )

    # --- pet_food ---
    op.create_table(
        "pet_food",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("brand", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kcal_per_100g", sa.Double(), nullable=False),
        sa.Column("protein", sa.Double(), nullable=True),
        sa.Column("carbs", sa.Double(), nullable=True),
        sa.Column("fat", sa.Double(), nullable=True),
        sa.Column(
            "source",
            sa.Enum("seed", "fatsecret", "user", name="pet_food_source", create_type=False),
            nullable=False,
            server_default="seed",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("brand", "name", name="uq_pet_food_brand_name"),
    )
    op.create_index("ix_pet_food_brand", "pet_food", ["brand"])

    # --- notification_log ---
    op.create_table(
        "notification_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pet_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pet.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column(
            "payload",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "channel",
            sa.Enum("expo", "log", name="notification_channel", create_type=False),
            nullable=False,
            server_default="log",
        ),
    )
    op.create_index(
        "ix_notification_log_user_sent",
        "notification_log",
        ["user_id", sa.text("sent_at DESC")],
    )

    # --- device ---
    op.create_table(
        "device",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expo_token", sa.String(), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("ios", "android", "web", name="device_platform", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("expo_token", name="uq_device_expo_token"),
    )
    op.create_index("ix_device_user", "device", ["user_id"])


def downgrade() -> None:
    op.drop_table("device")
    op.drop_table("notification_log")
    op.drop_table("pet_food")
    op.drop_table("vet_visit")
    op.drop_table("calendar_task")
    op.drop_table("meal")
    op.execute("DROP TYPE IF EXISTS device_platform")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS pet_food_source")
    op.execute("DROP TYPE IF EXISTS calendar_task_kind")
    op.execute("DROP TYPE IF EXISTS meal_food_kind")
    op.execute("DROP TYPE IF EXISTS meal_source")
