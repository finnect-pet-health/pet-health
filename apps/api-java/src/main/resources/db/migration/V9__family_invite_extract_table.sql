-- V9__family_invite_extract_table.sql
-- 학습 자료 — DB 리팩토링 P3.
--
-- family.invite_code / invite_expires_at 두 컬럼을 별도 family_invite 테이블로
-- 추출 — 1:N 관계로 일반화 + 발급/사용 감사 로그 가능.
--
-- 학습 포인트
--   - 1:1 collapsed 모델 → 1:N 정규화의 정석.
--   - 데이터 보존 마이그: 기존 활성 invite 를 새 테이블로 INSERT 후 컬럼 DROP.
--   - PG 제약명은 relation 네임스페이스를 공유 → 같은 이름 재사용 시 기존
--     제약을 먼저 DROP 해야 함.

-- ===== 1. V1 의 uq_family_invite_code 제약 먼저 DROP =====
-- 이름 재사용을 위해. invite_code 컬럼은 backfill 후 단계 4 에서 DROP.
ALTER TABLE family DROP CONSTRAINT uq_family_invite_code;

-- ===== 2. family_invite 테이블 신설 =====
CREATE TABLE family_invite (
    id          UUID PRIMARY KEY,
    family_id   UUID         NOT NULL REFERENCES family (id) ON DELETE CASCADE,
    code        VARCHAR(16)  NOT NULL,
    expires_at  TIMESTAMPTZ  NOT NULL,
    created_by  UUID         REFERENCES "user" (id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    used_at     TIMESTAMPTZ,
    used_by     UUID         REFERENCES "user" (id) ON DELETE SET NULL,
    CONSTRAINT uq_family_invite_code UNIQUE (code)
);
CREATE INDEX ix_family_invite_family_created
    ON family_invite (family_id, created_at DESC);

-- ===== 3. 기존 활성 invite 를 family_invite 로 백필 =====
-- invite_code 가 NULL 이 아닌 family 만 마이그. expires_at NULL 이면 now()
-- 로 두어 즉시 만료 (안전한 기본값).
INSERT INTO family_invite (id, family_id, code, expires_at, created_by, created_at)
SELECT
    gen_random_uuid(),
    id,
    invite_code,
    COALESCE(invite_expires_at, now()),
    owner_id,
    created_at
FROM family
WHERE invite_code IS NOT NULL;

-- ===== 4. family 테이블 정리 =====
ALTER TABLE family DROP COLUMN invite_code;
ALTER TABLE family DROP COLUMN invite_expires_at;
