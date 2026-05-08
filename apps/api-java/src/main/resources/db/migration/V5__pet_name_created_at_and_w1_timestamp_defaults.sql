-- V5__pet_name_created_at_and_w1_timestamp_defaults.sql
-- 학습 자료 — DB 리팩토링 P0+P1 (audit 결과 기반).
--
-- P1) pet.name VARCHAR NULL — 펫 이름 저장 컬럼이 V1 부터 누락돼 있었음.
--     nullable 로 추가해 모바일 contract 비파괴 (점진 도입).
-- P1) pet.created_at TIMESTAMPTZ NOT NULL DEFAULT now() — 다른 W1 테이블과
--     일관. 기존 행은 마이그 시점 timestamp 로 backfill.
-- P0) "user".created_at / family.created_at 에 DEFAULT now() 보강 — 다른
--     테이블과 달리 DEFAULT 가 없어 애플리케이션 누락 시 INSERT 실패 위험.
--
-- 검증: ALTER 만 사용 (DROP / CHANGE TYPE 없음) → 다운타임 0, rollback 시
-- 추가된 컬럼/디폴트만 제거하면 됨.

ALTER TABLE pet ADD COLUMN name VARCHAR;
ALTER TABLE pet ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE "user" ALTER COLUMN created_at SET DEFAULT now();
ALTER TABLE family ALTER COLUMN created_at SET DEFAULT now();
