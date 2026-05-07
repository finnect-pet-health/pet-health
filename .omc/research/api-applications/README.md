# API 신청 현황 인덱스

> W1 freeze 기준: 2026-05-07 | W2-v2 시작: 2026-05-08

이 디렉토리는 PetFinect 프로젝트에서 사용하는 외부 API 신청 상태를 추적합니다.
실제 키·시크릿은 `.env` 파일에만 보관하며, 여기에는 계정 정보·채널·타임라인만 기록합니다.

---

## 통합 상태 테이블

| # | 통합          | 우선순위   | 상태             | 담당자     | 응답 예상     |
|---|---------------|-----------|-----------------|-----------|-------------|
| 1 | Caretail      | Critical  | 신청 안 함       | -         | 수일~수주    |
| 2 | 카카오 디벨로퍼 | High      | 신청 안 함       | -         | 즉시         |
| 3 | data.go.kr    | High      | 신청 안 함       | -         | 자동~수시간  |
| 4 | FatSecret     | Mid       | 신청 안 함       | -         | 즉시 (보통)  |
| 5 | Expo (푸시)   | Low       | 신청 안 함       | -         | 즉시         |

---

## 오늘 (2026-05-07) 필수 액션

1. **[Critical] Caretail** — peachbite.pet / caretail.net 컨택폼으로 이메일 발송
2. **[High] 카카오** — developers.kakao.com 앱 생성 + 4개 키 `.env` 입력
3. **[High] data.go.kr** — 회원가입 + 동물병원 데이터셋 활용신청

---

## 파일 목록

- [01-caretail.md](01-caretail.md) — Caretail 반려동물 건강 데이터 (Critical)
- [02-kakao.md](02-kakao.md) — 카카오 디벨로퍼 소셜 로그인 (High)
- [03-data-go-kr.md](03-data-go-kr.md) — 공공데이터포털 동물병원 (High)
- [04-fatsecret.md](04-fatsecret.md) — FatSecret 영양 데이터 (Mid)
- [05-expo.md](05-expo.md) — Expo 푸시 알림 (Low)

---

## 상태 범례

- `신청 안 함` — 아직 미신청
- `신청 중 (YYYY-MM-DD)` — 신청 완료, 응답 대기
- `승인 완료 (YYYY-MM-DD)` — 키 발급 완료
- `거절 (YYYY-MM-DD)` — 거절됨 (Fallback 전환 필요)
