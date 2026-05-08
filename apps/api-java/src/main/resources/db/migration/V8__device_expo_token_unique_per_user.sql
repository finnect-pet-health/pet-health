-- V8__device_expo_token_unique_per_user.sql
-- 학습 자료 — DB 리팩토링 P3.
--
-- expo_token 의 글로벌 UNIQUE 를 (user_id, expo_token) 복합 UNIQUE 로 완화.
--
-- 배경
--   - Expo Push 토큰은 같은 단말의 앱 재설치 / 캐시 클리어 / 토큰 재발급 시
--     동일 값이 다른 user 에게 재할당될 수 있음 (Expo 공식 문서).
--   - 글로벌 UNIQUE 면 그 INSERT 가 실패 → 알림 등록이 막힘.
--   - 같은 user 가 같은 토큰을 두 번 등록하는 것만 막으면 충분.
--
-- 학습 포인트
--   - DROP CONSTRAINT … 로 기존 UNIQUE 제거.
--   - ADD CONSTRAINT … UNIQUE (col1, col2) 로 복합 UNIQUE.
--   - device 라우트는 아직 미구현 (placeholder) — 데이터 영향 0, 코드 영향 0.

ALTER TABLE device DROP CONSTRAINT uq_device_expo_token;
ALTER TABLE device ADD  CONSTRAINT uq_device_user_expo_token UNIQUE (user_id, expo_token);
