-- V10__w2_nutrition_normalize.sql
-- 학습 자료 — DB 리팩토링 P4 (미사용 W2 테이블 정합성).
--
-- (1) meal_food_kind ENUM 한글 → 영문 키
--     i18n 시 라벨 매핑이 클라이언트로 위임됨 + 코드 검색/타입 안전성 ↑.
--     PG 10+ 의 ALTER TYPE … RENAME VALUE 로 in-place 변경 (DROP/CREATE 불필요).
--
-- (2) pet_food.{protein,carbs,fat} → {protein_per_100g, carbs_per_100g, fat_per_100g}
--     kcal_per_100g 와 단위 표기 통일. meal.{protein_g,...} (1회분 g 단위) 와도 명확히 구별.
--
-- (3) 영양 정보 컬럼 DOUBLE PRECISION → NUMERIC(10, 2)
--     부동소수점 누적 오차 회피. 영양정보는 100g 당 ~ 자릿수 충분.
--     PG 가 implicit cast → 데이터 손실 없음.
--
-- 학습 포인트
--   - ALTER TYPE … RENAME VALUE : ENUM 값 in-place rename (drop/create 불요).
--   - ALTER COLUMN … TYPE NUMERIC : 부동소수점 → 정밀 십진수 (financial/measurement).
--   - meal/pet_food 는 service/route 미참조 (placeholder) → 데이터 영향 0,
--     코드 영향은 entity/model/enum 만.

-- ===== 1. meal_food_kind ENUM 한글값을 영문 키로 rename =====
ALTER TYPE meal_food_kind RENAME VALUE '사료'   TO 'kibble';
ALTER TYPE meal_food_kind RENAME VALUE '간식'   TO 'treat';
ALTER TYPE meal_food_kind RENAME VALUE '일반식' TO 'regular';
ALTER TYPE meal_food_kind RENAME VALUE '처방식' TO 'prescription';

-- ===== 2. pet_food 단위 컬럼명 통일 (per 100g) =====
ALTER TABLE pet_food RENAME COLUMN protein TO protein_per_100g;
ALTER TABLE pet_food RENAME COLUMN carbs   TO carbs_per_100g;
ALTER TABLE pet_food RENAME COLUMN fat     TO fat_per_100g;

-- ===== 3. 영양 정보 컬럼 DOUBLE PRECISION → NUMERIC(10, 2) =====
ALTER TABLE meal     ALTER COLUMN qty_g     TYPE NUMERIC(10, 2);
ALTER TABLE meal     ALTER COLUMN kcal      TYPE NUMERIC(10, 2);
ALTER TABLE meal     ALTER COLUMN protein_g TYPE NUMERIC(10, 2);
ALTER TABLE meal     ALTER COLUMN carbs_g   TYPE NUMERIC(10, 2);
ALTER TABLE meal     ALTER COLUMN fat_g     TYPE NUMERIC(10, 2);

ALTER TABLE pet_food ALTER COLUMN kcal_per_100g     TYPE NUMERIC(10, 2);
ALTER TABLE pet_food ALTER COLUMN protein_per_100g  TYPE NUMERIC(10, 2);
ALTER TABLE pet_food ALTER COLUMN carbs_per_100g    TYPE NUMERIC(10, 2);
ALTER TABLE pet_food ALTER COLUMN fat_per_100g      TYPE NUMERIC(10, 2);
