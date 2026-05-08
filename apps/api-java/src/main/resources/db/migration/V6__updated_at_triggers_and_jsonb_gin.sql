-- V6__updated_at_triggers_and_jsonb_gin.sql
-- 학습 자료 — DB 리팩토링 P2.
--
-- 1) updated_at 컬럼 + trigger 추가 (변경 감사 표준화).
--    hospital 은 V3 부터 이미 updated_at 보유 → 트리거만 attach.
--    user/family/pet/diagnosis_event 은 컬럼 신설 + 트리거.
--
-- 2) JSONB 컬럼 검색 가속 — GIN 인덱스 (@>, ?, ?| 연산자).
--    pet.conditions  : ["allergy_chicken", ...] 검색용.
--    diagnosis_event.top_results : [{"label":..., "score":...}] 라벨 필터.
--
-- 학습 포인트
--   - PL/pgSQL trigger function: NEW 변수 = 변경 후 행. RETURN NEW 로 commit.
--   - BEFORE UPDATE = INSERT/DELETE 영향 없음. updated_at 은 INSERT 시
--     DB DEFAULT now() 가 셋팅, UPDATE 시 trigger 가 갱신.
--   - GIN access method = 역색인. 일반 b-tree 와 다른 query plan.
--     `pg_indexes WHERE indexdef LIKE '%USING gin%'` 로 확인.

-- ===== 1. trigger function (모든 가변 테이블 공통) =====
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ===== 2. updated_at 컬럼 추가 (hospital 제외) =====
ALTER TABLE "user"          ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE family          ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE pet             ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE diagnosis_event ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- ===== 3. BEFORE UPDATE 트리거 (5 테이블) =====
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

-- ===== 4. JSONB GIN 인덱스 =====
CREATE INDEX ix_pet_conditions_gin
    ON pet USING GIN (conditions);
CREATE INDEX ix_diagnosis_event_top_results_gin
    ON diagnosis_event USING GIN (top_results);
