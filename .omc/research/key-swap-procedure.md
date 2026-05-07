# Kakao Mock → Real OAuth Swap Procedure

W1 Day 2까지 카카오 OAuth는 `MockKakaoOAuthClient` 어댑터를 통해 동작한다.
실제 카카오 디벨로퍼 키가 발급되면 아래 5단계로 swap한다 (코드 변경 0).

## 0. 사전 조건

- `apps/api/app/integrations/kakao/factory.py:get_kakao_client` 가
  `settings.app_env != "development"` 이고 `KAKAO_USE_MOCK != "1"` 일 때
  `RealKakaoOAuthClient` 를 반환하도록 이미 구현됨.
- `apps/api/app/integrations/kakao/real.py` 본문은 W2에서 채운다 (현재 token
  교환 단계까지만 작성, userinfo parse는 `NotImplementedError`).

## 1. `.env` 갱신

`apps/api/.env` 에 아래 5개 키를 추가/갱신한다.

```dotenv
APP_ENV=staging                    # development 가 아니면 됨
KAKAO_USE_MOCK=0
KAKAO_REST_API_KEY=<from-kakao-developer>
KAKAO_NATIVE_APP_KEY=<from-kakao-developer>
KAKAO_CLIENT_SECRET=<from-kakao-developer>
KAKAO_REDIRECT_URI=https://api.petfinect/v1/auth/kakao/callback
```

`KAKAO_USE_MOCK=0` 이 핵심 — 이 값이 `1` 이면 `factory.get_kakao_client`
가 여전히 mock을 반환한다.

## 2. API 재시작

```bash
docker compose restart api
# 또는 dev:
cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

`get_kakao_client()` 가 이제 `RealKakaoOAuthClient` 를 반환한다.

## 3. 검증 A — Mock 코드 거부

가짜 코드 `mock-user-1` 으로 호출 시 실 카카오 서버가 거부 → 502
`KAKAO_UNREACHABLE` (또는 token endpoint가 400) 반환되면 swap이 적용된 증거.

```bash
curl -i localhost:8000/v1/auth/kakao \
  -H 'content-type: application/json' \
  -d '{"auth_code":"mock-user-1","redirect_uri":"http://localhost"}'
# expect: 502 Bad Gateway, error.code=KAKAO_UNREACHABLE
```

## 4. 검증 B — 모바일 실 로그인

- Expo 앱 → /login 화면에서 "Mock User 1" 대신 카카오 OAuth 버튼(W2)
- 카카오 → redirect_uri로 authCode 반환 → API → 200 + 정상 access/refresh

## 5. 롤백

키 발급 이슈 / 장애 시:

```dotenv
KAKAO_USE_MOCK=1   # 즉시 mock으로 회귀
```

API 재시작.

---

### W2 의존 항목 (별도 카드)

`apps/api/app/integrations/kakao/real.py` 의 token 교환 이후 userinfo JSON →
`KakaoUser` 매핑이 `NotImplementedError` 로 남아 있다. W2에서 본문을 채운다.

키 swap 절차 자체는 본 문서로 종결.
