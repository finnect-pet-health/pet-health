-- V7__hospital_licensed_at_to_date.sql
-- 학습 자료 — DB 리팩토링 P2.
--
-- hospital.licensed_at VARCHAR → DATE 변환.
-- 원천 (data.go.kr LCPMT_YMD) 가 'YYYYMMDD' 문자열이라 V3 부터 VARCHAR 로
-- 두었으나, ETL 단계에서 파싱해 DATE 로 적재하는 게 자연스럽다 (정렬/조건절
-- 단순화 + 형식 일관성 강제).
--
-- USING expression 은 다음 케이스를 안전하게 변환:
--   NULL          → NULL
--   ''            → NULL  (NULLIF 로 통일)
--   '20200101'    → DATE 2020-01-01  (YYYYMMDD)
--   '2020-01-01'  → DATE 2020-01-01  (ISO)
--   기타 형식      → NULL  (data quality 문제는 ETL 측에서 잡고 DB 는 보수적)
--
-- 학습 포인트
--   - ALTER COLUMN ... TYPE ... USING : 컬럼 타입 변경 시 변환식 명시.
--   - 정규식 매칭 (~ 연산자) + CASE 로 안전한 데이터 변환 패턴.

ALTER TABLE hospital
    ALTER COLUMN licensed_at TYPE DATE
    USING (
        CASE
            WHEN NULLIF(licensed_at, '') IS NULL          THEN NULL
            WHEN licensed_at ~ '^[0-9]{8}$'               THEN to_date(licensed_at, 'YYYYMMDD')
            WHEN licensed_at ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN licensed_at::date
            ELSE NULL
        END
    );
