-- V4__diagnosis_event.sql
-- W3 — diagnosis_event 테이블 + modality/action enum.
-- Alembic 0004_diagnosis_event.py 와 1:1.

CREATE TYPE diagnosis_modality AS ENUM ('image', 'audio', 'timeseries');
CREATE TYPE diagnosis_action AS ENUM ('immediate', 'schedule', 'observe');

CREATE TABLE diagnosis_event (
    id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pet (id) ON DELETE CASCADE,
    modality diagnosis_modality NOT NULL,
    s3_ref VARCHAR NOT NULL,
    top_results JSONB NOT NULL DEFAULT '[]',
    action diagnosis_action NOT NULL,
    confidence_top1 DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_diagnosis_event_pet_created
    ON diagnosis_event (pet_id, created_at DESC);
