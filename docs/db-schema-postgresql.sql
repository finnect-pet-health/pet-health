-- =============================================================
-- PetFinect — PostgreSQL 16 + PostGIS 3.4 DB schema
-- Source: apps/api-java/src/main/resources/db/migration/V1~V7.sql
--
-- 학습 포인트
--   1) PostgreSQL ENUM 타입 (CREATE TYPE ... AS ENUM)
--   2) JSONB 컬럼 + DEFAULT '[]' / '{}'
--   3) PostGIS geometry(Point, 4326) + GiST 공간 인덱스
--   4) 복합 기본키 (composite PK)
--   5) 부분 인덱스 (partial index, WHERE 절)
--   6) ON DELETE 정책 (CASCADE / RESTRICT / SET NULL)
--   7) UNIQUE 제약과 인덱스의 차이
-- =============================================================


-- =============================================================
-- 1. Extensions
-- =============================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS postgis;    -- geometry / ST_DWithin / ...


-- =============================================================
-- 2. ENUM 타입
--   - ALTER TYPE ... ADD VALUE 로 값 추가 가능 (제거 불가).
--   - 문자열 + CHECK 제약 대비 메모리/디스크 효율 ↑.
-- =============================================================
CREATE TYPE member_role          AS ENUM ('owner', 'member');
CREATE TYPE pet_species          AS ENUM ('dog', 'cat', 'other');

CREATE TYPE meal_source          AS ENUM ('fatsecret', 'custom', 'seed');
CREATE TYPE meal_food_kind       AS ENUM ('사료', '간식', '일반식', '처방식');
CREATE TYPE calendar_task_kind   AS ENUM ('meal', 'walk', 'medicine', 'vet', 'custom');
CREATE TYPE pet_food_source      AS ENUM ('seed', 'fatsecret', 'user');
CREATE TYPE notification_channel AS ENUM ('expo', 'log');
CREATE TYPE device_platform      AS ENUM ('ios', 'android', 'web');

CREATE TYPE diagnosis_modality   AS ENUM ('image', 'audio', 'timeseries');
CREATE TYPE diagnosis_action     AS ENUM ('immediate', 'schedule', 'observe');


-- =============================================================
-- 3. W1 — 사용자 / 가족 / 펫
-- =============================================================

-- 3.1 사용자
--   - "user" 는 SQL 예약어 → 큰따옴표로 quoting 필요.
--   - kakao_id UNIQUE = 카카오 OAuth 식별자.
CREATE TABLE "user" (
    id              UUID PRIMARY KEY,
    kakao_id        VARCHAR     NOT NULL,
    email           VARCHAR,
    name            VARCHAR     NOT NULL,
    profile_image   VARCHAR,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- V5: DEFAULT 보강
    last_login_at   TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- V6: + BEFORE UPDATE trigger
    CONSTRAINT uq_user_kakao_id UNIQUE (kakao_id)
);
CREATE INDEX ix_user_kakao_id ON "user" (kakao_id);

-- 3.2 가족 (1 owner = 1 가족 그룹)
--   - owner_id ON DELETE RESTRICT = 가족이 있는 동안 owner 삭제 불가.
--   - invite_code 는 16자 이내 + UNIQUE.
CREATE TABLE family (
    id                  UUID PRIMARY KEY,
    name                VARCHAR     NOT NULL,
    owner_id            UUID        NOT NULL REFERENCES "user" (id) ON DELETE RESTRICT,
    invite_code         VARCHAR(16),
    invite_expires_at   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),  -- V5: DEFAULT 보강
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),  -- V6: + BEFORE UPDATE trigger
    CONSTRAINT uq_family_invite_code UNIQUE (invite_code)
);

-- 3.3 가족 멤버 (M:N)
--   - 복합 PK: (family_id, user_id) — 같은 사람이 같은 가족에 두 번 못 들어감.
--   - 양쪽 FK 모두 CASCADE → 가족/유저 삭제 시 멤버십도 정리.
CREATE TABLE family_member (
    family_id   UUID        NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    user_id     UUID        NOT NULL REFERENCES "user"  (id) ON DELETE CASCADE,
    role        member_role NOT NULL,
    joined_at   TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (family_id, user_id)
);
CREATE INDEX ix_family_member_user_id ON family_member (user_id);

-- 3.4 펫
--   - conditions 는 JSONB 배열. 예: ["allergy_chicken", "diabetes"]
--   - JSONB 인덱스가 필요하면 GIN 인덱스 별도 구성.
CREATE TABLE pet (
    id          UUID PRIMARY KEY,
    family_id   UUID            NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    species     pet_species     NOT NULL DEFAULT 'dog',
    name        VARCHAR,                                       -- V5: 펫 이름 (nullable)
    breed       VARCHAR,
    dob         DATE,
    weight      DOUBLE PRECISION,
    neutered    BOOLEAN         NOT NULL DEFAULT FALSE,
    conditions  JSONB           NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT now(),        -- V5: 일관성
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT now()         -- V6: + BEFORE UPDATE trigger
);


-- =============================================================
-- 4. W2 — 식사 / 캘린더 / 병원 방문 / 사료 DB / 알림 / 디바이스
--   ⚠ Phase 9 시점 기준 Java/Python 백엔드 어느 쪽도 service/route
--      레이어에서 호출하지 않는 placeholder. 학습 자료 + 향후 W2 라우트
--      구현을 위한 사전 스키마.
-- =============================================================

-- 4.1 식사 로그
CREATE TABLE meal (
    id          UUID PRIMARY KEY,
    pet_id      UUID            NOT NULL REFERENCES pet (id) ON DELETE CASCADE,
    ts          TIMESTAMPTZ     NOT NULL,
    source      meal_source     NOT NULL,
    food_id     VARCHAR,
    food_name   VARCHAR         NOT NULL,
    qty_g       DOUBLE PRECISION NOT NULL,
    kcal        DOUBLE PRECISION,
    protein_g   DOUBLE PRECISION,
    carbs_g     DOUBLE PRECISION,
    fat_g       DOUBLE PRECISION,
    note        VARCHAR,
    food_kind   meal_food_kind,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT now()
);
CREATE INDEX ix_meal_pet_ts ON meal (pet_id, ts);

-- 4.2 캘린더 일정
--   - 부분 인덱스: assignee_id IS NOT NULL 인 행만 인덱싱 → 인덱스 크기 ↓.
--   - 같은 user/pet 의 FK 인데 ON DELETE 정책이 다른 게 학습 포인트:
--       pet_id      → SET NULL (펫 삭제돼도 일정 자체는 보존)
--       assignee_id → SET NULL (담당자 빠지면 미할당으로 둠)
--       created_by  → RESTRICT (작성자가 있는 동안 삭제 불가)
CREATE TABLE calendar_task (
    id              UUID PRIMARY KEY,
    family_id       UUID                NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    pet_id          UUID                         REFERENCES pet    (id) ON DELETE SET NULL,
    title           VARCHAR             NOT NULL,
    kind            calendar_task_kind  NOT NULL,
    due_at          TIMESTAMPTZ         NOT NULL,
    assignee_id     UUID                         REFERENCES "user"(id) ON DELETE SET NULL,
    created_by      UUID                NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    completed_at    TIMESTAMPTZ,
    notes           VARCHAR,
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT now()
);
CREATE INDEX ix_calendar_task_family_due ON calendar_task (family_id, due_at);
CREATE INDEX ix_calendar_task_assignee
    ON calendar_task (assignee_id)
    WHERE assignee_id IS NOT NULL;

-- 4.3 병원 방문 기록
--   - DESC 인덱스: "최근 방문 순" 페이지네이션 최적화.
CREATE TABLE vet_visit (
    id              UUID PRIMARY KEY,
    pet_id          UUID         NOT NULL REFERENCES pet (id) ON DELETE CASCADE,
    visited_at      TIMESTAMPTZ  NOT NULL,
    hospital_name   VARCHAR,
    reason          VARCHAR,
    cost_krw        INTEGER,
    attachments     JSONB        NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX ix_vet_visit_pet_visited ON vet_visit (pet_id, visited_at DESC);

-- 4.4 사료 카탈로그
--   - 복합 UNIQUE: 같은 브랜드의 같은 제품명 중복 방지.
CREATE TABLE pet_food (
    id              UUID PRIMARY KEY,
    brand           VARCHAR             NOT NULL,
    name            VARCHAR             NOT NULL,
    kcal_per_100g   DOUBLE PRECISION    NOT NULL,
    protein         DOUBLE PRECISION,
    carbs           DOUBLE PRECISION,
    fat             DOUBLE PRECISION,
    source          pet_food_source     NOT NULL DEFAULT 'seed',
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),
    CONSTRAINT uq_pet_food_brand_name UNIQUE (brand, name)
);
CREATE INDEX ix_pet_food_brand ON pet_food (brand);

-- 4.5 알림 로그
--   - payload JSONB = 알림 종류별 가변 데이터 (스키마리스).
CREATE TABLE notification_log (
    id          UUID PRIMARY KEY,
    user_id     UUID                 NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
    pet_id      UUID                          REFERENCES pet    (id) ON DELETE SET NULL,
    kind        VARCHAR              NOT NULL,
    payload     JSONB                NOT NULL DEFAULT '{}',
    sent_at     TIMESTAMPTZ          NOT NULL DEFAULT now(),
    channel     notification_channel NOT NULL DEFAULT 'log'
);
CREATE INDEX ix_notification_log_user_sent ON notification_log (user_id, sent_at DESC);

-- 4.6 디바이스 (Expo push token 등)
CREATE TABLE device (
    id              UUID PRIMARY KEY,
    user_id         UUID            NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
    expo_token      VARCHAR         NOT NULL,
    platform        device_platform NOT NULL,
    last_seen_at    TIMESTAMPTZ     NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    CONSTRAINT uq_device_expo_token UNIQUE (expo_token)
);
CREATE INDEX ix_device_user ON device (user_id);


-- =============================================================
-- 5. W3 — 동물병원 (PostGIS)
-- =============================================================
-- 학습 포인트
--   - geometry(Point, 4326) — 컬럼 modifier 로 타입 + SRID 강제.
--     · 4326 = WGS84 (위경도). 한국 공공데이터 EPSG:5174 는 ETL 단계에서 변환.
--   - GiST 인덱스 = 공간 인덱스. ST_DWithin / && / <-> 연산자 가속.
--   - 일반 컬럼 인덱스(btree) 와 다른 access method.
CREATE TABLE hospital (
    id              UUID PRIMARY KEY,
    mgmt_no         VARCHAR             NOT NULL,
    name            VARCHAR             NOT NULL,
    road_addr       VARCHAR             NOT NULL DEFAULT '',
    lot_addr        VARCHAR             NOT NULL DEFAULT '',
    zip             VARCHAR             NOT NULL DEFAULT '',
    tel             VARCHAR             NOT NULL DEFAULT '',
    status          VARCHAR             NOT NULL DEFAULT '',
    licensed_at     DATE,                                                 -- V7: VARCHAR → DATE
    authority_code  VARCHAR             NOT NULL DEFAULT '',
    location        geometry(Point, 4326),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT now(),
    CONSTRAINT uq_hospital_mgmt_no UNIQUE (mgmt_no)
);
CREATE INDEX ix_hospital_location ON hospital USING GIST (location);
CREATE INDEX ix_hospital_status   ON hospital (status);


-- =============================================================
-- 6. W3 — AI 진단 이벤트
-- =============================================================
-- 학습 포인트
--   - top_results JSONB = AI 모델의 top-K 추론 결과 (라벨 + 확률).
--   - DESC 인덱스 (pet_id, created_at DESC) — 최신순 페이지네이션 최적.
CREATE TABLE diagnosis_event (
    id                  UUID PRIMARY KEY,
    pet_id              UUID                NOT NULL REFERENCES pet (id) ON DELETE CASCADE,
    modality            diagnosis_modality  NOT NULL,
    s3_ref              VARCHAR             NOT NULL,
    top_results         JSONB               NOT NULL DEFAULT '[]',
    action              diagnosis_action    NOT NULL,
    confidence_top1     DOUBLE PRECISION    NOT NULL,
    created_at          TIMESTAMPTZ         NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ         NOT NULL DEFAULT now()  -- V6
);
CREATE INDEX ix_diagnosis_event_pet_created
    ON diagnosis_event (pet_id, created_at DESC);


-- =============================================================
-- 7. V6 — updated_at trigger + JSONB GIN 인덱스
-- =============================================================
-- 학습 포인트
--   - PL/pgSQL trigger function: NEW = 변경 후 행. RETURN NEW 로 commit.
--   - BEFORE UPDATE 시점 → INSERT/DELETE 영향 없음.
--   - GIN access method = 역색인. JSONB 의 @>, ? , ?| 연산자 가속.

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5 가변 테이블 트리거
CREATE TRIGGER trg_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_family_updated_at BEFORE UPDATE ON family
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_pet_updated_at BEFORE UPDATE ON pet
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_diagnosis_event_updated_at BEFORE UPDATE ON diagnosis_event
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_hospital_updated_at BEFORE UPDATE ON hospital
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- JSONB GIN
CREATE INDEX ix_pet_conditions_gin            ON pet USING GIN (conditions);
CREATE INDEX ix_diagnosis_event_top_results_gin ON diagnosis_event USING GIN (top_results);


-- =============================================================
-- 부록. 참고 쿼리
-- =============================================================

-- A. 반경 3km 내 영업중 병원 distance ASC top 10
-- SELECT id, name,
--   ST_Distance(location::geography, ST_MakePoint(127.0276, 37.4979)::geography) AS dist_m
-- FROM hospital
-- WHERE status = '정상' AND location IS NOT NULL
--   AND ST_DWithin(location::geography, ST_MakePoint(127.0276, 37.4979)::geography, 3000)
-- ORDER BY dist_m ASC
-- LIMIT 10;

-- B. 펫의 최근 진단 5건
-- SELECT modality, action, confidence_top1, top_results, created_at
-- FROM diagnosis_event
-- WHERE pet_id = '<uuid>'
-- ORDER BY created_at DESC
-- LIMIT 5;

-- C. JSONB containment: "allergy_chicken" 조건 가진 펫
-- SELECT id, breed FROM pet WHERE conditions @> '["allergy_chicken"]';
