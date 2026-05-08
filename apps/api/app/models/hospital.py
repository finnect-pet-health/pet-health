import uuid
from datetime import date, datetime

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Hospital(Base):
    __tablename__ = "hospital"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    mgmt_no: Mapped[str] = mapped_column(sa.String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    road_addr: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")
    lot_addr: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")
    zip: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")
    tel: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")
    status: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")
    # V7: VARCHAR(YYYYMMDD) → DATE. ETL 측 _parse_ymd 가 파싱.
    licensed_at: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    authority_code: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
