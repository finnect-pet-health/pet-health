"""0003_hospital_postgis

W3-v2 head-start — `hospital` 테이블 + PostGIS POINT (SRID=4326) 컬럼 + spatial index.
ETL (`infra/etl/hospital_sync.py --upsert`) 가 data.go.kr 동물병원 OpenAPI rows 를
EPSG:5174 → 4326 변환 후 적재할 대상 테이블.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-07
"""
from collections.abc import Sequence

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "hospital",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mgmt_no", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("road_addr", sa.String(), nullable=False, server_default=""),
        sa.Column("lot_addr", sa.String(), nullable=False, server_default=""),
        sa.Column("zip", sa.String(), nullable=False, server_default=""),
        sa.Column("tel", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.String(), nullable=False, server_default=""),
        sa.Column("licensed_at", sa.String(), nullable=True),
        sa.Column("authority_code", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("mgmt_no", name="uq_hospital_mgmt_no"),
    )
    op.create_index(
        "ix_hospital_location",
        "hospital",
        ["location"],
        postgresql_using="gist",
    )
    op.create_index("ix_hospital_status", "hospital", ["status"])


def downgrade() -> None:
    op.drop_index("ix_hospital_status", table_name="hospital")
    op.drop_index("ix_hospital_location", table_name="hospital")
    op.drop_table("hospital")
