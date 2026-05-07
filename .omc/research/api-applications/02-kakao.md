# 02. 카카오 디벨로퍼 — 소셜 로그인 / 카카오톡

| 항목       | 내용                           |
|-----------|-------------------------------|
| 우선순위   | **High** (모바일·백엔드 공통 의존) |
| 담당자     | (채울 것)                     |
| 현재 상태  | 신청 안 함                    |

---

## 상태 이력

- [ ] 신청 안 함
- [ ] 앱 생성 완료 (날짜: )
- [ ] 키 발급 완료 (날짜: )
- [ ] 심사 거절 (날짜: )

---

## 계정 정보

| 항목            | 값                                   |
|----------------|--------------------------------------|
| 카카오 계정     | (신청에 사용할 카카오 이메일)          |
| 앱 이름         | PetFinect                            |
| 앱 ID           | (앱 생성 후 채울 것)                  |
| REST API 키     | `.env` → `KAKAO_REST_API_KEY`        |
| Native App 키   | `.env` → `KAKAO_NATIVE_APP_KEY`      |
| JavaScript 키   | `.env` → `KAKAO_JS_KEY`              |
| Client Secret   | `.env` → `KAKAO_CLIENT_SECRET`       |

---

## 신청 일자

> 미입력 — 앱 생성 후 채울 것

---

## 신청 채널

- URL: https://developers.kakao.com/
- 방법: 카카오 계정으로 로그인 → "내 애플리케이션" → "애플리케이션 추가하기"
- 앱 정보 입력:
  - 앱 이름: `PetFinect`
  - 회사/팀명: (팀명)
  - 카테고리: 건강/피트니스
  - iOS 번들 ID: `app.petfinect`
  - Android 패키지명: `app.petfinect`

---

## 발급 키 목록 (4종)

1. **REST API 키** — 서버-사이드 API 호출
2. **네이티브 앱 키** — iOS / Android SDK
3. **JavaScript 키** — 웹 SDK (웹뷰)
4. **Client Secret** — 보안 강화 (선택, 권장)

---

## Redirect URI 설정

```
https://api.petfinect/v1/auth/kakao/callback
```

> 개발 환경 추가: `http://localhost:3000/auth/kakao/callback`

---

## 신청 시 첨부 자료

- 별도 첨부 불필요 (즉시 발급)
- 앱 이름, 카테고리, 플랫폼 정보만 입력하면 4개 키 즉시 확인 가능

---

## 응답 예상 시간

**즉시** — 앱 생성 즉시 4개 키 발급됨

---

## Fallback 계획

- 카카오 로그인 미연동 시: 이메일/비밀번호 로그인으로 대체
- 시연 목적이면 카카오 테스트 계정(개발자 계정 자체)으로 로그인 데모 가능

---

## 다음 액션 (오늘 — 2026-05-07)

> **오늘 안으로 developers.kakao.com 접속 → 앱 생성 → 4개 키 복사 → `.env` 입력.**
> 5분 내 완료 가능. 오늘 W2-v2 시작 전 반드시 완료.
