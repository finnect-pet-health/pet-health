# W1 Plan · Auth Foundation + External-API Spike (Mock-First)

> 기간: 2026-05-02(금) ~ 2026-05-07(목), 6일 · 4–5인 팀
> 상위 plan: `~/.claude/plans/ai-compressed-codd.md` § 10 W1 / `docs/specs/auth-and-family.md` § 9
> 모드: 인터뷰 결과 — 범위 W1만 / Kakao·Caretail 키 둘 다 미발급 / mock 인증 전 경로 동작 목표

---

## 1. Requirements Summary

W1 종료(5.7) 시점에 **mobile → cloud API → Postgres** 의 인증·가족 happy-path가 mock 카카오 어댑터로 E2E 동작하고, 외부 API 키 신청 트랙이 진행 중이며, Caretail / KakaoMap 두 spike의 결론이 문서화되어 있어야 한다. 키 발급 후 코드 한 군데(어댑터 환경변수)만 바꾸면 실 카카오 OAuth로 swap되도록 추상화한다.

### 1.1 In Scope
- 카카오 디벨로퍼 + 케어테일 API 신청 제출(승인 대기 시작) — Day 1 첫 작업.
- DB 스키마: `User`, `Family`, `FamilyMember`, `Pet` (4개) + Alembic `0001_init` 마이그레이션.
- 인증: `KakaoOAuthClient` 인터페이스 + `MockKakaoOAuthClient`(authCode → fake user) + 실 클라이언트 stub.
- API 실구현: `POST /v1/auth/kakao`, `POST /v1/auth/refresh`, `POST /v1/auth/logout`, `GET /v1/me`, Family CRUD(`POST/GET /v1/families`, `POST /v1/families/{id}/invite`, `POST /v1/families/join`, `GET /v1/families/{id}/members`).
- RBAC 의존성: `require_family(role="member"|"owner")` FastAPI Depends.
- JWT util: HS256, access 15m / refresh 14d, Redis `refresh:{user_id}:{jti}` 회전 정책.
- Mobile: 로그인 화면(mock 버튼) → `/v1/auth/kakao` 호출 → token SecureStore 저장 → `/v1/me` 호출 → 가족 선택/생성 → 메인.
- Spike 1: Caretail OAuth 문서/응답 스키마 정리 + `HealthProvider` 추상 + `MockHealthProvider`(시드 7일 데이터).
- Spike 2: KakaoMap RN bridge — Expo prebuild 가능 여부 판단 + 막힐 시 WebView fallback 결정 문서화.
- 단위 테스트: `auth-and-family.md` § 8 체크리스트 8개 중 5개 이상 통과.

### 1.2 Out of Scope (W2 이후)
- 실 카카오 OAuth 연동(키 발급 후 W2 첫 카드).
- 실제 Caretail 데이터 폴링 워커, RQ 스케줄러.
- Pet CRUD 풀 구현(W1은 모델·POST/GET만, 수정·삭제는 W2).
- 헬스 분석 모델, 의료비 예측, 병원 매칭, 후원, 결제.
- Sentry/모니터링 연동.

### 1.3 Constraints (인터뷰 확정)
- API 키 둘 다 미발급 → 모든 외부 통합은 인터페이스 + mock 우선.
- 4–5인 팀 → 백엔드(2) / 모바일(1) / AI·인프라(1) / 리드·PM(1) 분담.
- 6일 캘린더 → Day 6은 통합·문서·W2 카드 정리 전용(신규 코드 동결).

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `docker compose up -d postgres redis` 후 `alembic upgrade head` 로 4개 테이블 생성 확인 | `psql ... -c "\dt"` 출력에 `user, family, family_member, pet` 존재 |
| AC2 | `POST /v1/auth/kakao` 에 `{auth_code: "mock-user-1", redirect_uri: "..."}` 보내면 `{access, refresh, user}` 200 응답 | `pytest apps/api/tests/test_auth.py::test_mock_kakao_login` |
| AC3 | 같은 mock authCode 두 번째 로그인은 **같은 user_id** 로 upsert | `pytest ::test_kakao_login_idempotent` |
| AC4 | `POST /v1/auth/refresh` 사용 직후 직전 refresh 재사용은 **401 revoked** | `pytest ::test_refresh_rotation` |
| AC5 | `GET /v1/me` 가 Authorization 헤더 없으면 401, 유효 토큰이면 가족 목록 포함 200 | `pytest ::test_me_authorization` |
| AC6 | `member` 역할 사용자가 `POST /v1/families/{id}/invite` 호출 시 403 `FORBIDDEN` | `pytest ::test_owner_only_invite` |
| AC7 | 만료된 invite_code 로 `/v1/families/join` 호출 시 410 `INVITE_EXPIRED` | `pytest ::test_expired_invite` |
| AC8 | Mobile dev 빌드에서 mock 로그인 → 가족 생성 → 홈 진입까지 1회 성공 (Expo Go on physical device 또는 Android emulator) | 시연 영상 30초, `docs/w1-demo.md` 에 첨부 |
| AC9 | `apps/api/app/integrations/health/mock.py` 가 7일치 시드 HealthSnapshot을 결정적으로 반환 | `pytest apps/api/tests/test_mock_health_provider.py` |
| AC10 | `docs/spikes/caretail-spike.md` 에 ① OAuth 절차, ② 5개 핵심 endpoint 응답 예, ③ rate-limit 정책, ④ MVP polling 주기 결정 기록 | 수동 리뷰 (lead) |
| AC11 | `docs/spikes/kakao-map-spike.md` 에 ① Expo prebuild 결과, ② SDK 작동 여부, ③ 실패 시 WebView fallback 시안 기록 | 수동 리뷰 (lead) |
| AC12 | 카카오 디벨로퍼 앱 신청 영수증 + 케어테일 API 신청 메일 사본 첨부 | `.omc/research/api-applications/` 에 스크린샷 |

---

## 3. Implementation Steps

### 3.1 Day 1 (5.2 금) — Kickoff & Foundations

> 차주 모든 일정의 차단 요소(키 신청, DB 스키마, 모델·인터페이스 결정)를 풀어두는 날.

#### 트랙 A · 외부 신청 (lead, 30분~1시간)
- [ ] 카카오 디벨로퍼: 비즈 앱 등록 → 닉네임/이메일/프로필 동의 항목 신청 → REST/Native key 발급 → `.env` 임시 채움.
  - 참조: `docs/specs/auth-and-family.md` § 2.2.
- [ ] 케어테일: 공식 API 사용 신청 폼 제출 (회사/팀명·연락처·예상 트래픽 작성). 승인 메일 도착 시까지 대기.
- [ ] 신청 영수증/캡처를 `.omc/research/api-applications/` 에 저장 (AC12).

#### 트랙 B · 백엔드 ORM + Alembic (backend lead)
- [ ] `apps/api/app/models/__init__.py` 생성. 다음 4개 모델을 작성:
  - `apps/api/app/models/user.py` — `User(id UUID, kakao_id str unique, email, name, profile_image, created_at, last_login_at)`
  - `apps/api/app/models/family.py` — `Family(id, name, owner_id FK→user.id, invite_code unique nullable, invite_expires_at)`
  - `apps/api/app/models/family_member.py` — `FamilyMember(family_id FK, user_id FK, role enum('owner','member'), joined_at)` PK=(family_id, user_id), index user_id.
  - `apps/api/app/models/pet.py` — `Pet(id, family_id FK, species enum default 'dog', breed, dob, weight, neutered, conditions JSONB)`. (W1은 스키마만, CRUD는 트랙 D)
  - 스펙 출처: `docs/specs/auth-and-family.md` § 3.
- [ ] `alembic init apps/api/alembic` → `alembic.ini` postgres dsn은 환경변수 사용. `apps/api/alembic/env.py` 가 `app.database.Base.metadata` 를 import.
- [ ] `alembic revision --autogenerate -m "0001_init"` → 4개 테이블 + 필요한 인덱스/제약조건 검증 후 commit.
- [ ] `alembic upgrade head` 로컬 검증 (AC1).

#### 트랙 C · JWT util + Mock OAuth 클라이언트 (backend dev)
- [ ] `apps/api/app/security/jwt.py`:
  - `encode_access(user_id: UUID, fids: list[UUID], roles: dict[UUID, str]) -> str`
  - `decode_access(token: str) -> AccessClaims` (만료/위조 시 `JWTError`)
  - `issue_refresh(user_id) -> tuple[token, jti]` + Redis `setex refresh:{user_id}:{jti}` (TTL 14d)
  - `rotate_refresh(token)`, `revoke_refresh(token)`.
- [ ] `apps/api/app/integrations/kakao/__init__.py` interface:
  ```python
  class KakaoOAuthClient(Protocol):
      async def exchange_code(self, code: str, redirect_uri: str) -> KakaoUser: ...
  ```
- [ ] `apps/api/app/integrations/kakao/mock.py` — `MockKakaoOAuthClient`:
  - 입력 `auth_code` 형식: `"mock-user-{n}"` → 결정적으로 `KakaoUser(kakao_id=f"mock_{n}", name=f"테스트유저{n}", email=...)` 반환.
  - 잘못된 형식이면 `KakaoExchangeError("invalid_code")`.
- [ ] `apps/api/app/integrations/kakao/real.py` — `RealKakaoOAuthClient` stub (httpx 요청 골격만, W2 채움).
- [ ] `apps/api/app/integrations/kakao/factory.py` — env `APP_ENV` 또는 `KAKAO_USE_MOCK=1` 일 때 mock, 아니면 real.

#### 트랙 D · HealthProvider 인터페이스 (AI/infra)
- [ ] `apps/api/app/integrations/health/__init__.py`:
  ```python
  class HealthProvider(Protocol):
      async def fetch_window(self, pet_id: UUID, since: datetime) -> list[HealthSnapshot]: ...
  ```
  스펙: `docs/specs/02-health-analysis.md` § 2.2 의 스키마 그대로 사용 (Pydantic 모델).
- [ ] `apps/api/app/integrations/health/mock.py` — `MockHealthProvider`:
  - 시드 시나리오: "보리(시바, 4세)" 14일치 활동·심박·수면·체중. anomaly_score가 마지막 3일 0.7+ 로 떨어지도록 설계.
  - 결정적(시드 = pet_id 해시) → AC9 가능.
- [ ] `apps/api/tests/test_mock_health_provider.py` 1개 (AC9).

#### 트랙 E · Mobile 베이스 (mobile dev)
- [ ] `apps/mobile/src/api/client.ts` 가 axios 인스턴스 + interceptor (Authorization 헤더 주입, 401 시 refresh 재시도) 가지도록 보강.
- [ ] `apps/mobile/src/auth/store.ts` (zustand) — `{accessToken, refreshToken, user, families}` + SecureStore 직렬화.
- [ ] `apps/mobile/app/login.tsx` 신규 — 카카오 로고 버튼 + dev 환경에서 "mock-user-1/2/3" 셀렉터 노출.
- [ ] `apps/mobile/app/_layout.tsx` 가 토큰 부재 시 `/login` 리다이렉트.

**Day 1 종료 조건**: AC1 통과, JWT util/mock 클라이언트가 완성되어 트랙 D Day 2가 막힘 없이 시작 가능.

---

### 3.2 Day 2 (5.3 토) — Auth 라우터 실구현

#### 트랙 A · `/v1/auth/*` 실구현 (backend lead)
- [ ] `apps/api/app/api/v1/auth.py` 의 4개 스텁(`apps/api/app/api/v1/auth.py:18-34`)을 실 구현으로 교체.
  - `kakao_login`: factory → `exchange_code` → `User` upsert(by kakao_id) → access+refresh 발급 → response.
  - `refresh_token`: refresh decode → Redis 검증 → 새 pair 발급 → 직전 jti 삭제.
  - `logout`: refresh의 jti만 Redis 삭제.
  - `GET /v1/me` 신규: 현재 user + `families: [{id, name, role}]` 반환.
- [ ] `apps/api/app/security/deps.py`:
  - `current_user(token: str = Depends(oauth2_scheme)) -> User`
  - `require_family(family_id: UUID, role: Literal["member","owner"]="member") -> FamilyMember`
- [ ] `apps/api/tests/test_auth.py` — AC2/3/4/5 커버.

#### 트랙 B · Family CRUD (backend dev)
- [ ] `apps/api/app/api/v1/families.py` 의 4개 스텁(`apps/api/app/api/v1/families.py:11-28`)을 실 구현으로 교체:
  - `POST /v1/families`: 생성 + 본인을 owner로 자동 가입.
  - `GET /v1/families`: 내가 속한 모든 가족 + 멤버 수.
  - `POST /v1/families/{id}/invite`: 8자 base32 코드 생성, ttl 후 만료 시각 저장. **owner 전용**.
  - `POST /v1/families/join`: 코드 검증 + 만료 검사(410) + 기존 멤버 차단 + member로 join.
  - `GET /v1/families/{id}/members` 신규: 가족 멤버 리스트 (member 이상).
- [ ] `apps/api/tests/test_families.py` — AC6/7 + 마지막 owner 탈퇴 차단 케이스.

#### 트랙 C · Mobile 로그인 플로우 (mobile dev)
- [ ] `apps/mobile/src/api/auth.ts` — `loginWithMock(code)`, `refreshTokens()`, `me()`, `families.create/list/join`.
- [ ] `apps/mobile/app/login.tsx` 가 mock 버튼 클릭 → API 호출 → store 저장 → `expo-router` `/` 로 이동.
- [ ] `apps/mobile/app/onboarding/family.tsx` — 가족 없음 시 "가족 만들기 / 코드로 참여" 분기.

#### 트랙 D · Spike 시작 (AI/infra)
- [ ] Caretail 공식 문서 정리 시작. 응답 스키마 mocking 까지. `docs/spikes/caretail-spike.md` 초안 작성.
- [ ] KakaoMap RN bridge: `expo prebuild` 시도 → 결과 기록.

**Day 2 종료 조건**: AC2~AC5 통과. mobile에서 mock 로그인 → /me 응답 화면에 user.name이 보임.

---

### 3.3 Day 3 (5.4 일) — Family + Spike 가속

- [ ] AC6/AC7 통과 (test_families).
- [ ] Mobile 가족 생성/참여 화면 + 가족 전환 UI.
- [ ] `apps/api/app/api/v1/pets.py` 에 `POST /v1/pets`, `GET /v1/pets` 만 구현(AC외, W2 준비).
- [ ] Caretail spike 진행 — OAuth 토큰 교환까지 sandbox 흉내(httpx 모킹), `docs/spikes/caretail-spike.md` § 1~3 채움.
- [ ] KakaoMap spike — Expo prebuild 결과 따라 분기 결정. 막히면 WebView fallback PoC 1개 화면 제작.

---

### 3.4 Day 4 (5.5 월, 어린이날) — 통합 + Spike 마감

- [ ] AC8 시연 1회 — physical device or emulator. 영상 30초.
- [ ] Caretail spike 마감 — `docs/spikes/caretail-spike.md` 최종(AC10).
- [ ] KakaoMap spike 마감 — `docs/spikes/kakao-map-spike.md` 최종(AC11).
- [ ] `MockHealthProvider` 시드 데이터 검증 (AC9).
- [ ] 카카오/케어테일 신청 진행 상황 점검 — 1:1 문의가 필요하면 lead 가 처리.

---

### 3.5 Day 5 (5.6 화) — 단위 테스트 + 보강

- [ ] `auth-and-family.md` § 8 체크리스트 8개 중 최소 5개 통과 (AC2~7 + AC9 누적).
- [ ] `apps/api/tests/test_rbac.py` — `require_family` 엣지 케이스 (가족 없음 404, 다른 가족 ID 404, role 부족 403).
- [ ] CI 셋업: `.github/workflows/api.yml` — `pytest`, `ruff`, `mypy` (백엔드만, mobile은 W2).
- [ ] `apps/mobile/src/components/AuthGate.tsx` 정리, dev 환경 mock 셀렉터 UX 개선.

---

### 3.6 Day 6 (5.7 목) — Freeze · 문서 · W2 카드

> **신규 코드 금지**. 통합·문서·다음 주 카드 분해만.

- [ ] AC1~AC12 전부 점검. 미통과 항목은 W2 첫 카드로 이월.
- [ ] `docs/w1-retrospective.md` — 잘 된 것/막힌 것/W2에 옮길 것.
- [ ] OpenAPI 스키마 export (`fastapi` `--openapi-url`) → `docs/api/openapi-w1.json`.
- [ ] `packages/shared-types/` codegen 첫 실행, mobile에서 import 확인.
- [ ] W2 작업 카드 초안 (`.omc/plans/w2-pet-health-nutrition.md`) — Pet/Meal/CalendarTask CRUD + 헬스 폴링 + Stage 1 anomaly 모델.

---

## 4. Risks & Mitigations

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | 카카오 디벨로퍼 비즈 앱 승인 지연 (~3–5영업일) | 高 | 中 | mock 어댑터로 W1 전체를 차단 없이 진행. 키 도착 즉시 W2 첫날 swap. |
| R2 | 케어테일 API 신청이 W4까지도 미승인 | 中 | 高 | `MockHealthProvider`로 5.25 시연까지 커버. 시연에 "공식 연동 진행 중" 디스클레이머 명시. |
| R3 | KakaoMap RN bridge가 Expo Go 로 안 됨 | 高 | 中 | Day 4 결정 시점에 WebView fallback으로 전환. 본선 전 EAS Build로 native 재시도. |
| R4 | 4–5명 중 1명 어린이날(5.5) 부재 | 中 | 中 | Day 4 작업을 spike 마감 + 통합으로 구성, 신규 기능 작업은 Day 1–3에 몰아둠. |
| R5 | Alembic autogenerate 가 PostGIS 확장(이후 Hospital용) 충돌 | 低 | 低 | W1 모델에는 PostGIS 사용 안 함. 확장 활성화는 W3 hospitals migration 별도. |
| R6 | JWT 비밀키 dev 디폴트 그대로 prod 노출 | 低 | 高 | `app.config.Settings.jwt_secret` 디폴트 `"dev-only-secret"` 인 상태에서 `APP_ENV != development` 면 startup assertion 으로 죽이기. |
| R7 | mobile 토큰 저장이 SecureStore vs MMKV 혼선 | 低 | 中 | 결정: 토큰만 SecureStore, 비-민감 캐시는 MMKV. `docs/w1-decisions.md` 에 기록. |
| R8 | Day 6 freeze 가 깨지고 신규 기능이 들어옴 | 中 | 中 | Day 5 종료 시 lead 가 PR 머지 권한 동결. Day 6 PR은 docs/test 만. |

---

## 5. Verification Steps

### 5.1 자동
```bash
cd apps/api
docker compose up -d postgres redis
uv pip install -e ".[dev]"
alembic upgrade head
pytest -v --cov=app --cov-fail-under=70
ruff check .
mypy app
```

### 5.2 수동 (AC8)
1. `apps/mobile` 에서 `pnpm start` → Expo Go 실행.
2. 로그인 화면 → "mock-user-1" 선택 → "테스트유저1" 이름이 홈에서 보이는지 확인.
3. 가족 만들기 → "보리네" 입력 → 메인 진입.
4. 30초 화면 녹화 → `.omc/research/w1-demo.mp4`.

### 5.3 수동 (Spike 검수)
- lead 가 `docs/spikes/caretail-spike.md`, `docs/spikes/kakao-map-spike.md` 를 읽고 § 6 위험 행이 채워졌는지 확인.

### 5.4 종료 점검 (Day 6 PM)
- AC1~AC12 12개 중 통과 수 기록.
- 통과 < 9 → W2 첫날 보강 카드 삽입.
- 통과 ≥ 9 → W2 정상 진입.

---

## 6. Team Allocation (4–5인)

| 트랙 | 인력 | 주요 산출 |
|---|---|---|
| Backend Lead | 1 | ORM·Alembic·auth 라우터·JWT·RBAC deps |
| Backend Dev | 1 | Family CRUD·tests·OpenAPI export·CI |
| Mobile Dev | 1 | login·family onboarding·api client·token store |
| AI/Infra | 1 | HealthProvider·MockHealthProvider·Caretail/KakaoMap spike |
| Lead/PM (5명일 때) | 1 | 외부 API 신청·일정 점검·spike 검수·docs 마감·시연 |

> 4명 운영 시 Lead/PM 역할을 Backend Lead 가 겸직.

---

## 7. File Map (생성·수정 대상)

```
apps/api/
  alembic.ini                             [new]
  alembic/env.py                          [new]
  alembic/versions/0001_init.py           [new]
  app/models/{user,family,family_member,pet}.py  [new]
  app/security/jwt.py                     [new]
  app/security/deps.py                    [new]
  app/integrations/kakao/{__init__,mock,real,factory}.py  [new]
  app/integrations/health/{__init__,mock}.py              [new]
  app/api/v1/auth.py                      [rewrite, current stub at apps/api/app/api/v1/auth.py:18-34]
  app/api/v1/families.py                  [rewrite, current stub at apps/api/app/api/v1/families.py:11-28]
  app/api/v1/pets.py                      [partial: POST/GET only]
  tests/test_auth.py                      [new]
  tests/test_families.py                  [new]
  tests/test_rbac.py                      [new]
  tests/test_mock_health_provider.py      [new]

apps/mobile/
  app/login.tsx                           [new]
  app/onboarding/family.tsx               [new]
  app/_layout.tsx                         [edit, redirect on no-token]
  src/api/client.ts                       [edit, interceptor]
  src/api/auth.ts                         [new]
  src/api/families.ts                     [new]
  src/auth/store.ts                       [new]
  src/components/AuthGate.tsx             [new]

docs/
  spikes/caretail-spike.md                [new]
  spikes/kakao-map-spike.md               [new]
  w1-decisions.md                         [new, MMKV vs SecureStore 등]
  w1-retrospective.md                     [new]
  api/openapi-w1.json                     [generated]

.omc/research/
  api-applications/{kakao,caretail}.png   [new]
  w1-demo.mp4                             [new]

.github/workflows/api.yml                 [new]
```

---

## 8. Done Definition

- [ ] AC1~AC12 중 ≥ 9개 통과.
- [ ] `docs/w1-retrospective.md` 작성.
- [ ] `.omc/plans/w2-pet-health-nutrition.md` 초안 존재.
- [ ] 카카오/케어테일 신청 영수증 보관 (.omc/research/api-applications/).
- [ ] mobile mock 로그인 데모 영상 1회.
- [ ] CI 통과 (pytest + ruff + mypy).

---

## 9. Open Questions (실행 전 결정 필요)

1. JWT 비밀키 — W1 dev는 .env, prod는 어디(Cloudflare Secrets / 1Password)? → Day 1 lead 결정.
2. 단위 테스트 커버리지 임계 — 70% 초기. W2에서 80%로 올림.
3. Refresh 토큰 회전 시 grace window(직전 token 5초 허용)? → 보수적으로 즉시 폐기 채택.
4. mobile 빌드 타깃 — Expo Go 우선(W1) / EAS Build(W2 후반).

---

## 10. Changelog

- 2026-05-02 — 초안 작성 (인터뷰 기반: W1 only, 키 둘 다 미발급, 4–5인, mock-first 동작 목표).
