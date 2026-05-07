-- V2__w2_models.sql
-- W2 — meal/calendar_task/vet_visit/pet_food/notification_log/device + 6 enums
-- Alembic 0002_w2_models.py 와 1:1.

-- enums
CREATE TYPE meal_source AS ENUM ('fatsecret', 'custom', 'seed');
CREATE TYPE meal_food_kind AS ENUM ('사료', '간식', '일반식', '처방식');
CREATE TYPE calendar_task_kind AS ENUM ('meal', 'walk', 'medicine', 'vet', 'custom');
CREATE TYPE pet_food_source AS ENUM ('seed', 'fatsecret', 'user');
CREATE TYPE notification_channel AS ENUM ('expo', 'log');
CREATE TYPE device_platform AS ENUM ('ios', 'android', 'web');

-- meal
CREATE TABLE meal (
    id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pet (id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL,
    source meal_source NOT NULL,
    food_id VARCHAR,
    food_name VARCHAR NOT NULL,
    qty_g DOUBLE PRECISION NOT NULL,
    kcal DOUBLE PRECISION,
    protein_g DOUBLE PRECISION,
    carbs_g DOUBLE PRECISION,
    fat_g DOUBLE PRECISION,
    note VARCHAR,
    food_kind meal_food_kind,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_meal_pet_ts ON meal (pet_id, ts);

-- calendar_task
CREATE TABLE calendar_task (
    id UUID PRIMARY KEY,
    family_id UUID NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    pet_id UUID REFERENCES pet (id) ON DELETE SET NULL,
    title VARCHAR NOT NULL,
    kind calendar_task_kind NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    assignee_id UUID REFERENCES "user" (id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES "user" (id) ON DELETE RESTRICT,
    completed_at TIMESTAMPTZ,
    notes VARCHAR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_calendar_task_family_due ON calendar_task (family_id, due_at);
CREATE INDEX ix_calendar_task_assignee
    ON calendar_task (assignee_id)
    WHERE assignee_id IS NOT NULL;

-- vet_visit
CREATE TABLE vet_visit (
    id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pet (id) ON DELETE CASCADE,
    visited_at TIMESTAMPTZ NOT NULL,
    hospital_name VARCHAR,
    reason VARCHAR,
    cost_krw INTEGER,
    attachments JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_vet_visit_pet_visited ON vet_visit (pet_id, visited_at DESC);

-- pet_food
CREATE TABLE pet_food (
    id UUID PRIMARY KEY,
    brand VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    kcal_per_100g DOUBLE PRECISION NOT NULL,
    protein DOUBLE PRECISION,
    carbs DOUBLE PRECISION,
    fat DOUBLE PRECISION,
    source pet_food_source NOT NULL DEFAULT 'seed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_pet_food_brand_name UNIQUE (brand, name)
);
CREATE INDEX ix_pet_food_brand ON pet_food (brand);

-- notification_log
CREATE TABLE notification_log (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
    pet_id UUID REFERENCES pet (id) ON DELETE SET NULL,
    kind VARCHAR NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    channel notification_channel NOT NULL DEFAULT 'log'
);
CREATE INDEX ix_notification_log_user_sent ON notification_log (user_id, sent_at DESC);

-- device
CREATE TABLE device (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
    expo_token VARCHAR NOT NULL,
    platform device_platform NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_device_expo_token UNIQUE (expo_token)
);
CREATE INDEX ix_device_user ON device (user_id);
