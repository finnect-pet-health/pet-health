-- V1__init.sql
-- W1 — auth + family + pet (Alembic 0001_init.py 와 1:1)
-- 2026-05-08 작성. UUID 는 gen_random_uuid() (pgcrypto), JSONB 는 PostgreSQL 네이티브.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- enums
CREATE TYPE member_role AS ENUM ('owner', 'member');
CREATE TYPE pet_species AS ENUM ('dog', 'cat', 'other');

-- user
CREATE TABLE "user" (
    id UUID PRIMARY KEY,
    kakao_id VARCHAR NOT NULL,
    email VARCHAR,
    name VARCHAR NOT NULL,
    profile_image VARCHAR,
    created_at TIMESTAMPTZ NOT NULL,
    last_login_at TIMESTAMPTZ,
    CONSTRAINT uq_user_kakao_id UNIQUE (kakao_id)
);
CREATE INDEX ix_user_kakao_id ON "user" (kakao_id);

-- family
CREATE TABLE family (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    owner_id UUID NOT NULL REFERENCES "user" (id) ON DELETE RESTRICT,
    invite_code VARCHAR(16),
    invite_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_family_invite_code UNIQUE (invite_code)
);

-- family_member (composite PK)
CREATE TABLE family_member (
    family_id UUID NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
    role member_role NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (family_id, user_id)
);
CREATE INDEX ix_family_member_user_id ON family_member (user_id);

-- pet
CREATE TABLE pet (
    id UUID PRIMARY KEY,
    family_id UUID NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    species pet_species NOT NULL DEFAULT 'dog',
    breed VARCHAR,
    dob DATE,
    weight DOUBLE PRECISION,
    neutered BOOLEAN NOT NULL DEFAULT FALSE,
    conditions JSONB NOT NULL DEFAULT '[]'
);
