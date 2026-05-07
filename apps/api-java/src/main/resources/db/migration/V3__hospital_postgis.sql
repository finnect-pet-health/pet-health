-- V3__hospital_postgis.sql
-- W3 — hospital 테이블 + PostGIS POINT(SRID 4326) + GiST spatial index.
-- Alembic 0003_hospital_postgis.py 와 1:1.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE hospital (
    id UUID PRIMARY KEY,
    mgmt_no VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    road_addr VARCHAR NOT NULL DEFAULT '',
    lot_addr VARCHAR NOT NULL DEFAULT '',
    zip VARCHAR NOT NULL DEFAULT '',
    tel VARCHAR NOT NULL DEFAULT '',
    status VARCHAR NOT NULL DEFAULT '',
    licensed_at VARCHAR,
    authority_code VARCHAR NOT NULL DEFAULT '',
    location geometry(Point, 4326),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_hospital_mgmt_no UNIQUE (mgmt_no)
);

CREATE INDEX ix_hospital_location ON hospital USING GIST (location);
CREATE INDEX ix_hospital_status ON hospital (status);
