"""0001_init

Revision ID: 0001
Revises:
Create Date: 2026-05-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- user ---
    op.create_table(
        "user",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("kakao_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("profile_image", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("kakao_id", name="uq_user_kakao_id"),
    )
    op.create_index("ix_user_kakao_id", "user", ["kakao_id"])

    # --- family ---
    op.create_table(
        "family",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("invite_code", sa.String(16), nullable=True),
        sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("invite_code", name="uq_family_invite_code"),
    )

    # --- family_member ---
    op.create_table(
        "family_member",
        sa.Column(
            "family_id",
            UUID(as_uuid=True),
            sa.ForeignKey("family.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("owner", "member", name="member_role", create_type=False),
            nullable=False,
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_family_member_user_id", "family_member", ["user_id"])

    # --- pet ---
    op.create_table(
        "pet",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "family_id",
            UUID(as_uuid=True),
            sa.ForeignKey("family.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "species",
            sa.Enum("dog", "cat", "other", name="pet_species", create_type=False),
            nullable=False,
            server_default="dog",
        ),
        sa.Column("breed", sa.String(), nullable=True),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("neutered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("conditions", JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_table("pet")
    op.drop_table("family_member")
    op.drop_table("family")
    op.drop_table("user")
    op.execute("DROP TYPE IF EXISTS pet_species")
    op.execute("DROP TYPE IF EXISTS member_role")
