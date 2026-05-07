# W2 Plan · Pet/Health/Nutrition CRUD + 헬스 폴링

> 기간: 2026-05-08(금) ~ 2026-05-14(목), 7일 · 4–5인 팀
> 상위 plan: `~/.claude/plans/ai-compressed-codd.md` § 10 W2 / `docs/specs/02-health-analysis.md` § 2~3 / `docs/specs/05-medical-budget-savings.md` § 2~3
> 모드: W1과 동일하게 mock-first 유지하되 Caretail/FatSecret 키 발급 시 즉시 swap. W1 freeze 해제 후 mypy 0 errors 회복 의무.

---

## 1. Requirements Summary

W2 종료(5.14) 시점에 **Pet·Family·일정 CRUD 풀**, **Caretail OAuth + RQ 폴링 워커(키 가정)**, **FatSecret 영양 입력**, **모바일 홈 화면(sparkline·칼로리)**, **푸시 알림 기본 동작**이 mock-first로 동작해야 한다. W1에서 동결한 mypy strict는 0 errors 회복하고, shared-types codegen 적용을 모바일 영양·일정 화면까지 확대한다. 모든 외부 통합은 W1과 동일하게 Provider 추상 + factory 패턴으로 swap-ready 상태를 유지하고, 키 발급 시 환경변수 한 줄로 real swap 가능한 구조를 보존한다.

### 1.1 In Scope

- `Pet` 모델 확장(메모, 알러지, photo_url) + `PATCH /v1/pets/{id}`, `DELETE /v1/pets/{id}` 풀 구현 + 가족 권한 검증.
- `Meal`, `CalendarTask`, `VetVisit` 3개 신규 모델 + `0002_w2_models` Alembic 마이그레이션.
- `POST/GET /v1/pets/{id}/meals`, `GET /v1/pets/{id}/meals/today` (FatSecret API + 자체 펫 사료 DB 시드 200건).
- `GET/POST/PATCH/DELETE /v1/calendar` (일정 CRUD + assignee 위임 + 완료 체크 + 가족 단위 조회).
- `RealHealthProvider`(Caretail OAuth client) 실 구현 — 키 발급 가정. 미발급 시 `MockHealthProvider` 폴백 자동 동작.
- RQ 워커 + scheduler(`apps/api/app/workers/health_poll.py`) — 사용자별 5분 주기 폴링, `HealthSnapshot` upsert + `daily_health` 일일 집계.
- `POST /v1/pets/{id}/health/sync` (폴링 강제 트리거) + `GET /v1/pets/{id}/health/snapshots` + `GET /v1/pets/{id}/health/daily` 실 응답.
- 푸시 알림 기본: Expo Notifications 연동 + `device_token` 등록 엔드포인트 + `notify_health_event` worker 함수(룰 기반 트리거: quality<0.3 30분 지속 시 "워치 미착용" 알림).
- 모바일 홈 화면: 활동/심박 7일 sparkline + 식단 칼로리 도넛 차트 + 빠른 식단 입력 모달.
- 모바일: Pet 편집/삭제 화면, 캘린더 주간 뷰, 식단 입력(검색 → 양 입력 → 저장).
- mypy 0 errors 회복(W1 freeze 해제) + ruff strict + coverage 80%+ 유지.
- shared-types codegen 적용 확대: meal/calendar/health 스키마까지.
- W3 카드 분해(`.omc/plans/w3-ai-anomaly-budget-hospital.md`) 초안 — Day 7 산출물.

### 1.2 Out of Scope (W3 이후)

- AI 헬스 분석 Stage 1 (anomaly 점수 산출, IsolationForest + z-score 앙상블) — `daily_health` 데이터만 W2에 쌓고 추론은 W3.
- Stage 2 질병 후보 LM, `/infer/disease` 로컬 AI 서버 mTLS 통신 — W3~W4.
- 의료비 예측식·`MedicalBudget` 모델·`/v1/budget` — W3.
- 병원 매칭(공공데이터 동물병원 ETL + 카카오맵) + `/v1/hospitals` — W3.
- 적금 권장 카드, 외부 가입 딥링크, 후원 결합 — W3 후반 ~ W4.
- 실 결제·오픈뱅킹 직접 연동 — Out (시연 범위 외).

### 1.3 Constraints

- W1 가정 유지: 카카오 키는 발급되었으나 Caretail 키는 *발급되었다고 가정*(R1 위험 표 참조). 미발급 시 mock 자동 폴백.
- 4–5인 팀 분담 그대로(백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1). 5.10 일요일은 작업 가능, 5.13 수요일은 mypy 회복 데이로 신규 코드 동결.
- Day 7(5.14)은 freeze + 통합 + W3 카드 + 시연 영상 갱신 전용. 신규 코드 금지.
- 의료/금융 디스클레이머는 W2 단계에서 *알림 본문·식단 추천 카드*에 이미 노출되어야 함(spec 05 § 10).

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `alembic upgrade head` 실행 시 `meal`, `calendar_task`, `vet_visit` 3개 테이블 + `pet` 테이블 컬럼 확장(memo, allergies jsonb, photo_url) 반영 | `psql -c "\dt"` 및 `\d pet` 출력 검증 |
| AC2 | `PATCH /v1/pets/{id}` 가 owner/member 모두 200, 다른 가족 사용자는 404 | `pytest apps/api/tests/test_pets.py::test_pet_patch_rbac` |
| AC3 | `DELETE /v1/pets/{id}` 는 owner 만 204, member 는 403 `FORBIDDEN` | `pytest ::test_pet_delete_owner_only` |
| AC4 | `POST /v1/pets/{id}/meals` 가 mock FatSecret 응답을 받아 `Meal{kcal, protein_g, carbs_g, fat_g}` 정상 저장 | `pytest apps/api/tests/test_meals.py::test_meal_create_with_mock_fatsecret` |
| AC5 | `GET /v1/pets/{id}/meals/today` 가 당일(KST) 칼로리 합·매크로 합 반환, 비어 있을 때 0 | `pytest ::test_meals_today_aggregate` |
| AC6 | 자체 펫 사료 DB 시드 200건이 `seed_pet_foods.py` 로 적재되고 `GET /v1/foods/search?q=로얄캐닌` 가 ≥ 1건 반환 | `pytest apps/api/tests/test_foods.py::test_pet_food_search` |
| AC7 | `POST /v1/calendar` 로 task 생성 후 `GET /v1/calendar?from=&to=` 가 가족 멤버 모두에게 동일 응답 | `pytest apps/api/tests/test_calendar.py::test_calendar_family_visibility` |
| AC8 | `PATCH /v1/calendar/{id}` 로 assignee 위임 + `done=true` 체크 시 `completed_at` UTC 기록 | `pytest ::test_calendar_assign_and_complete` |
| AC9 | Mock Caretail OAuth (`auth_code="mock-caretail-1"`) → `POST /v1/pets/{id}/health/sync` 호출 시 RQ 큐에 `health_poll` job enqueue + 30초 내 `HealthSnapshot` ≥ 12 row 적재 | `pytest apps/api/tests/test_health_polling.py::test_polling_enqueues_and_persists`(fakeredis + RQ SimpleWorker) |
| AC10 | `GET /v1/pets/{id}/health/daily?from=&to=` 가 활동 분/심박 평균/수면 deep ratio/체중을 일별 집계로 반환 (14일치 mock 데이터) | `pytest ::test_daily_health_aggregate` |
| AC11 | `POST /v1/devices` 로 expo push token 등록 후 `notify_health_event` 워커가 mock provider로 푸시 1건 발송, `notification_log` 1 row 적재 | `pytest apps/api/tests/test_notifications.py::test_health_event_push` |
| AC12 | Mobile 홈 화면에서 7일 활동 sparkline + 심박 sparkline + 칼로리 도넛(오늘) 동시 렌더 — 시연 영상 30초 | `.omc/research/w2-demo.mp4` 첨부, `docs/w2-demo.md` |
| AC13 | Mobile 식단 입력: 음식 검색 → 양 입력 → 저장 → 홈 칼로리 즉시 갱신 | 시연 영상 동일 회차 |
| AC14 | `mypy app` 0 errors (W1 strict freeze 해제), `ruff check .` 0 errors, `pytest --cov=app --cov-fail-under=80` 통과 | CI 로그 (`.github/workflows/api.yml`) green |
| AC15 | `packages/shared-types/` 가 W2 신규 스키마(meal, calendar_task, health_snapshot, daily_health)까지 포함하여 codegen 후 mobile 빌드 통과 | `pnpm -C apps/mobile typecheck` 0 errors |

> Done 임계: 15개 중 ≥ 12개 통과. 미통과는 W3 첫날 보강 카드.

---

## 3. Implementation Steps (Day 단위)

### 3.1 Day 1 (5.8 금) — Caretail RealProvider + RQ 워커 셋업 + FatSecret Mock

> W1 freeze 해제. mock-first 유지하되 키 발급 가정 코드 경로를 활성화.

#### 트랙 A · Caretail RealHealthProvider stub 채우기 (AI/infra)
- [ ] `apps/api/app/integrations/health/real.py` — W1 stub의 빈 메서드를 채움.
  - `async def authorize(redirect_uri) -> str` (state nonce + Caretail authorize URL)
  - `async def exchange_code(code, redirect_uri) -> CaretailTokens` (httpx `POST /oauth/token`)
  - `async def fetch_window(pet_id, since) -> list[HealthSnapshot]` (`GET /v1/pet-data/{external_id}` 호출, `docs/spikes/caretail-spike.md` § 2 응답 스키마 매핑)
  - 429 시 jitter exponential backoff (max 5 retries, base 0.5s), 401 시 refresh 자동 재시도 1회.
- [ ] `apps/api/app/integrations/health/factory.py` — `APP_ENV != production and CARETAIL_USE_MOCK in (1, "1", "true")` 시 mock, 아니면 real. 기본값 mock.
- [ ] 키 미발급 fallback: `RealHealthProvider.__init__` 에서 `CARETAIL_CLIENT_ID` 부재 시 `RuntimeWarning` + factory가 mock으로 자동 강등.

#### 트랙 B · RQ 워커 + 스케줄러 셋업 (backend lead)
- [ ] `apps/api/app/workers/__init__.py` + `apps/api/app/workers/queue.py` — RQ Queue("health_poll", "notifications") 정의, `redis_url=settings.redis_url`.
- [ ] `apps/api/app/workers/health_poll.py` — `def poll_pet_health(pet_id: UUID) -> int`:
  - factory → provider.fetch_window(since=last_ingest_ts)
  - HealthSnapshot upsert (pk=pet_id+ts), `daily_health` rollup 함수 호출.
  - 반환: 새로 적재된 row 수.
- [ ] `apps/api/app/workers/scheduler.py` — RQ Scheduler 또는 자체 cron tick(5분), 활성 사용자별 enqueue. dev 환경에서는 `manual_only=True` 로 disable.
- [ ] `apps/api/Dockerfile.worker` + `docker-compose.yml` 에 `worker` 서비스 추가(또는 기존에 있다면 명령어 보강).

#### 트랙 C · FatSecret Mock 클라이언트 (backend dev)
- [ ] `apps/api/app/integrations/fatsecret/__init__.py`:
  ```python
  class FoodProvider(Protocol):
      async def search(self, q: str, locale: str = "ko_KR") -> list[FoodItem]: ...
      async def get(self, food_id: str) -> FoodItem: ...
  ```
- [ ] `apps/api/app/integrations/fatsecret/mock.py` — 30개 결정적 시드(닭가슴살, 사과, 로얄캐닌 어덜트…) 반환.
- [ ] `apps/api/app/integrations/fatsecret/real.py` — OAuth1 stub(키 발급 가정). 시그니처는 채우되 W2 끝까지 mock 사용 가능.
- [ ] `apps/api/app/integrations/fatsecret/factory.py`.
- [ ] `apps/api/seeds/pet_foods.py` — 자체 펫 사료 DB **200건** 시드(브랜드·종류·kcal/100g·매크로). `python -m app.seeds.pet_foods` CLI.

#### 트랙 D · Pet 모델 확장 + Alembic (backend dev2 또는 lead 분담)
- [ ] `apps/api/app/models/pet.py` 에 `memo: str | None`, `allergies: list[str]` (JSONB), `photo_url: str | None` 추가.
- [ ] `apps/api/app/models/meal.py` 신규: `Meal(id, pet_id FK, ts, source enum('fatsecret','custom','seed'), food_id, food_name, qty_g, kcal, protein_g, carbs_g, fat_g, note)`.
- [ ] `apps/api/app/models/calendar_task.py` 신규: `CalendarTask(id, family_id FK, pet_id FK nullable, title, kind enum('meal','walk','medicine','vet','custom'), due_at, assignee_id FK→user, created_by FK, completed_at, notes)`.
- [ ] `apps/api/app/models/vet_visit.py` 신규: `VetVisit(id, pet_id FK, visited_at, hospital_name, reason, cost_krw, attachments jsonb)` — W2는 모델만, CRUD는 W3.
- [ ] `apps/api/app/models/pet_food.py` 신규: `PetFood(id, brand, name, kcal_per_100g, protein, carbs, fat, source enum('seed','fatsecret','user'))`.
- [ ] `apps/api/app/models/notification_log.py` 신규: `NotificationLog(id, user_id, pet_id, kind, payload jsonb, sent_at, channel enum('expo','log'))`.
- [ ] `apps/api/app/models/device.py` 신규: `Device(id, user_id, expo_token unique, platform enum, last_seen_at)`.
- [ ] `alembic revision --autogenerate -m "0002_w2_models"` → 검증 → commit (AC1).

**Day 1 종료 조건**: AC1 통과. 워커 컨테이너가 `redis-cli LPUSH` 받은 dummy job 1개를 소화하는 것까지 확인.

---

### 3.2 Day 2 (5.9 토) — Pets PATCH/DELETE + Meals POST/GET

#### 트랙 A · `/v1/pets` PATCH/DELETE (backend lead)
- [ ] `apps/api/app/api/v1/pets.py` 에 `PATCH /{id}`, `DELETE /{id}` 추가.
  - PATCH: 가족 멤버(member 이상) → 부분 업데이트(memo, allergies, weight, neutered, photo_url, conditions).
  - DELETE: **owner 전용** → soft delete(`deleted_at` 컬럼) — Pet 모델에 `deleted_at` 추가, 기존 GET/PATCH는 자동 필터.
- [ ] `apps/api/tests/test_pets.py` — AC2/AC3 + 마지막 펫 삭제 시 family 단위 스냅샷 보존 검증.

#### 트랙 B · Meals API (backend dev)
- [ ] `apps/api/app/api/v1/meals.py` 신규:
  - `POST /v1/pets/{pet_id}/meals` — body `{food_id?, food_name?, qty_g, ts?}`. food_id 없으면 FatSecret search 후 매칭, 매칭 실패 시 custom kcal 직접 입력 허용.
  - `GET /v1/pets/{pet_id}/meals?from&to` — 페이지네이션.
  - `GET /v1/pets/{pet_id}/meals/today` — 일일 집계(KST) `{date, kcal_total, protein_g, carbs_g, fat_g, items: [...]}`.
  - `GET /v1/foods/search?q=` — FoodProvider.search + 자체 PetFood 테이블 union, 결과 우선순위 [PetFood seed > FatSecret].
- [ ] `apps/api/tests/test_meals.py` — AC4, AC5.
- [ ] `apps/api/tests/test_foods.py` — AC6.

#### 트랙 C · 펫 사료 DB 시드 200건 (AI/infra 또는 lead)
- [ ] `apps/api/seeds/pet_foods.py` 구현 + 데이터 출처 메모(`docs/data/pet-foods-source.md`).
  - 브랜드 5개(로얄캐닌·힐스·오리젠·아카나·내추럴발란스 [추정]) × 라이프스테이지/사이즈 조합 ≈ 200.
  - kcal/100g, 단백/탄/지 분 표기. 출처: 각 사 공식 사이트 [추정 — Day 1 lead 가 1차 검수].

#### 트랙 D · Mobile Pet 편집 화면 (mobile dev)
- [ ] `apps/mobile/app/pets/[id]/edit.tsx` — 메모/알러지/체중/중성화 토글/사진 업로드(추후 S3, W2는 device cache).
- [ ] `apps/mobile/src/api/pets.ts` — patch/delete 훅.
- [ ] `apps/mobile/app/pets/[id]/index.tsx` — 상세 진입 + 편집/삭제 진입.

**Day 2 종료 조건**: AC2~AC6 통과.

---

### 3.3 Day 3 (5.10 일) — Calendar CRUD + 위임/완료

#### 트랙 A · `/v1/calendar` (backend lead)
- [ ] `apps/api/app/api/v1/calendar.py` 신규:
  - `POST /v1/calendar` — title, kind, due_at, assignee_id?, pet_id?
  - `GET /v1/calendar?from=&to=&family_id=` — 가족 단위 조회. `require_family(role="member")`.
  - `PATCH /v1/calendar/{id}` — 부분 수정 + assignee 변경 + `done=true` 시 `completed_at=utcnow()`.
  - `DELETE /v1/calendar/{id}` — 생성자 또는 owner 만.
- [ ] 검증: pet_id 가 있으면 pet 의 family_id 와 task family_id 가 일치해야 함(다른 가족 펫에 일정 못 걸기).
- [ ] `apps/api/tests/test_calendar.py` — AC7, AC8 + cross-family 차단 케이스.

#### 트랙 B · Mobile 캘린더 주간 뷰 (mobile dev)
- [ ] `apps/mobile/app/calendar/index.tsx` — 주간 grid + assignee 칩 + 완료 체크.
- [ ] `apps/mobile/app/calendar/new.tsx` — kind selector (산책·식사·약·진료·기타), 시간/담당자 선택.
- [ ] `apps/mobile/src/api/calendar.ts`.

#### 트랙 C · Mobile 식단 입력 화면 (mobile dev 또는 backend dev 보조)
- [ ] `apps/mobile/app/pets/[id]/meal-new.tsx` — 음식 검색 debounce 300ms → 결과 리스트 → 양(g) 입력 → 저장.
- [ ] `apps/mobile/src/api/meals.ts`.

#### 트랙 D · Caretail spike 보강 (AI/infra)
- [ ] `docs/spikes/caretail-spike.md` 에 W2 발견사항 (rate limit 실측, OAuth refresh 토큰 만료 정책) 추가.

**Day 3 종료 조건**: AC7, AC8 통과. mobile 캘린더 화면에서 task 생성·완료가 시각적으로 동작.

---

### 3.4 Day 4 (5.11 월) — 폴링 워커 실데이터 흐름 + daily_health 집계

#### 트랙 A · 폴링 엔드포인트 + 워커 통합 (backend lead + AI/infra)
- [ ] `apps/api/app/api/v1/health.py` 신규:
  - `POST /v1/pets/{id}/health/sync` — RQ enqueue, `{job_id}` 202.
  - `GET /v1/pets/{id}/health/snapshots?since=` — 최신 200개 또는 since 이후.
  - `GET /v1/pets/{id}/health/daily?from=&to=` — `daily_health` 집계 응답.
- [ ] `apps/api/app/services/health_aggregate.py` — `rollup_daily(pet_id, date)` 함수: 5분 스냅샷 → 일일 활동 분 합/심박 평균/수면 deep ratio/체중 last.
- [ ] `apps/api/app/models/daily_health.py` 신규 + Alembic `0003_daily_health`.
- [ ] `apps/api/tests/test_health_polling.py` — AC9, AC10. fakeredis + RQ `SimpleWorker(burst=True)`.

#### 트랙 B · Caretail Mock 14일 시드 보강 (AI/infra)
- [ ] `apps/api/app/integrations/health/mock.py` — 7일 → 14일 확장 (W1 베이스). anomaly 시그널을 day 12~14 활동 30%↓, 심박 평균 10%↑ 패턴으로 결정적 생성(W3 anomaly 모델 입력 검증용).

#### 트랙 C · shared-types codegen 확대 (backend dev)
- [ ] `packages/shared-types/openapi.ts` 재생성 — meal/calendar/health 스키마 포함.
- [ ] `apps/mobile/src/api/types.ts` 가 shared-types import 하도록 정리 (AC15).

**Day 4 종료 조건**: AC9, AC10 통과. `POST /v1/pets/{id}/health/sync` 호출 후 30초 내 14일 mock 데이터가 `health_snapshot` 테이블에 적재.

---

### 3.5 Day 5 (5.12 화) — Mobile 홈 sparkline + 칼로리 차트 + 알림

#### 트랙 A · 푸시 알림 인프라 (backend dev + mobile dev)
- [ ] `apps/api/app/api/v1/devices.py` — `POST /v1/devices {expo_token, platform}`.
- [ ] `apps/api/app/integrations/push/__init__.py` PushProvider Protocol.
- [ ] `apps/api/app/integrations/push/{mock,expo,factory}.py` — Expo Push API client.
- [ ] `apps/api/app/workers/notifications.py` — `notify_health_event(pet_id, kind, payload)`, 룰 트리거: `quality<0.3` 30분 지속 시 "워치 미착용" 알림.
- [ ] `apps/api/tests/test_notifications.py` — AC11.
- [ ] `apps/mobile/src/notifications/register.ts` — Expo Notifications permission 요청 + 토큰 등록 호출 + 백그라운드 핸들러.

#### 트랙 B · Mobile 홈 화면 (mobile dev)
- [ ] `apps/mobile/app/(tabs)/index.tsx` — 펫 셀렉터 + 7일 활동 sparkline + 7일 심박 sparkline + 오늘 칼로리 도넛(목표 대비) + 다음 일정 카드 + 빠른 식단/산책 입력 FAB.
- [ ] `apps/mobile/src/components/Sparkline.tsx` — `react-native-svg` 기반 [추정 — KakaoMap spike에서 같은 라이브러리 채택했다면 재사용].
- [ ] `apps/mobile/src/components/CalorieDonut.tsx`.
- [ ] 디스클레이머 텍스트: "참고용 추정치, 의료 진단 아님" 카드 푸터(spec 02 § 7, spec 05 § 10 의무).

#### 트랙 C · 의료비 통계 베이스라인 시드 *준비* (AI/infra, W3 선행)
- [ ] `apps/api/seeds/medical_baseline.py` — 품종·나이대 12 슬롯 × p50/p90 정적 테이블 시드 작성(KB펫금융보고서 등 출처 표기).
- [ ] **본 W2 In Scope 아님**(spec 05 § 8 W1 산출이지만 W1에서 누락된 경우만 W2로 이월). W3 예측식 코드는 작성하지 않음.

**Day 5 종료 조건**: AC11~AC13 통과. 모바일 홈에서 sparkline·도넛·일정 카드 동시 렌더 + 푸시 알림 1건 수신.

---

### 3.6 Day 6 (5.13 수) — mypy 0 errors 회복 + shared-types 적용 확대 + W3 카드 분해

> **신규 기능 코드 동결**. 타입·문서·테스트·차주 카드.

- [ ] `mypy app` 0 errors 회복(AC14).
  - W1 freeze 동안 누적된 `# type: ignore` 제거 우선순위 리스트 작성 → 반나절 정리.
  - `from __future__ import annotations` 일관 적용, Pydantic v2 `model_validate` 마이그레이션 잔여 정리.
- [ ] `ruff check . --fix` 후 잔여 violation 수동 정리.
- [ ] `pytest --cov-fail-under=80` 통과 확인. 부족 시 빈 곳에 happy-path 테스트 추가.
- [ ] `packages/shared-types` codegen 실행 + mobile typecheck 통과(AC15).
- [ ] `.omc/plans/w3-ai-anomaly-budget-hospital.md` 초안 — Stage 1 anomaly + medical budget 예측식 + 병원 매칭 + 적금 권장 카드를 9~10일 일정으로 분배 (5.15~5.21 W3 + 5.22~5.24 finalize 전 마지막 통합).

---

### 3.7 Day 7 (5.14 목) — Freeze · 통합 · 시연 영상 갱신

- [ ] AC1~AC15 점검표 갱신, 통과 ≥ 12 확인.
- [ ] `docs/w2-retrospective.md` — 잘 된 것/막힌 것/W3 이월.
- [ ] OpenAPI export → `docs/api/openapi-w2.json`.
- [ ] 시연 영상 갱신 — W1 demo + W2 흐름(로그인 → 가족 → 펫 → 식단 입력 → 캘린더 → 홈 sparkline → 알림 수신) 90초.
- [ ] `.omc/research/api-applications/` Caretail/FatSecret 키 발급 상태 스냅샷 갱신.

---

## 4. Risks & Mitigations

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | Caretail API 키가 W2 시작 시 미발급 (W1 가정 깨짐) | 中 | 高 | factory가 mock 자동 폴백, 워커는 mock provider 14일 시드로 동작. 시연 시 "공식 연동 진행 중" 디스클레이머 표기. AC9는 mock 경로로도 통과. |
| R2 | FatSecret OAuth1 승인 지연 | 高 | 中 | 자체 펫 사료 DB 200건 시드 우선순위 상승, FatSecret은 mock으로 W2 종료까지 운영 가능. AC4는 mock fixture로 통과. |
| R3 | RQ 워커가 dev 머신에서 `redis://localhost:6379` 외 환경에서 실패 | 中 | 中 | `docker compose up worker` 표준화, fakeredis 테스트 픽스처, README에 redis URL env 명시. |
| R4 | mypy 0 errors 회복이 Day 6 하루로 부족 | 中 | 中 | Day 1~5 동안 새 코드는 처음부터 strict 통과 룰 적용(PR checker). Day 6은 *잔여*만 정리. 부족 시 일부 모듈 `[strict-optional]` 한정 완화 + W3로 잔여 이월. |
| R5 | Expo push token 발급이 Expo Go 환경에서 제한 | 中 | 中 | EAS Build dev client 1회 빌드(R1 W1 KakaoMap과 합쳐 진행), 실패 시 시연은 mock provider + `notification_log` 행으로 대체. AC11은 mock provider 경로로 통과. |
| R6 | 캘린더 권한 체크 누락으로 cross-family 일정 노출 | 低 | 高 | `require_family` 의존 + cross-family 차단 테스트 명시(AC7), code review 필수. |
| R7 | shared-types codegen이 Pet/Meal 순환 참조 발생 | 低 | 中 | OpenAPI tag 분리 + `$ref` 유지, 실패 시 type alias 수동 패치 + W3에 자동화 재시도. |
| R8 | 5.10 일요일·5.13 수요일 인력 부재 | 中 | 中 | Day 3(일)은 캘린더 단일 트랙 위주로 부담 분산, Day 6(수)은 동결로 비동기 작업 가능. |
| R9 | 푸시 quiet hours 미구현 상태에서 한밤 알림 발송 | 低 | 中 | W2는 quiet hours 임시 hard-coded(22~07 차단), 정식 사용자 설정은 W3로 명시 이월. |
| R10 | 워커가 동일 pet_id 동시 enqueue로 race 발생 | 低 | 中 | RQ `Job.id=f"poll:{pet_id}:{slot}"` 5분 슬롯 dedup, upsert로 중복 안전. |

---

## 5. Verification Steps

### 5.1 자동
```bash
cd apps/api
docker compose up -d postgres redis worker
uv pip install -e ".[dev]"
alembic upgrade head
python -m app.seeds.pet_foods
pytest -v --cov=app --cov-fail-under=80
ruff check .
mypy app                       # 0 errors 회복(AC14)
cd ../../packages/shared-types
pnpm codegen
cd ../../apps/mobile
pnpm typecheck                 # AC15
```

### 5.2 수동 (AC12, AC13)
1. `pnpm -C apps/mobile start` → 로그인(mock) → 가족 → 펫 선택.
2. 식단 입력 → 칼로리 도넛 즉시 갱신.
3. 캘린더 → 산책 task 생성 → 가족 다른 계정 로그인에서 보임.
4. `POST /v1/pets/{id}/health/sync` → 30초 후 홈 sparkline 14일 데이터 표시.
5. 푸시 알림 1건 수신(테스트용 trigger).
6. 90초 시연 영상 → `.omc/research/w2-demo.mp4`.

### 5.3 종료 점검 (Day 7 PM)
- AC 통과 < 12 → W3 첫날 보강 카드 삽입.
- mypy 0 errors 미달 시 W3 첫날 보강.

---

## 6. Team Allocation (4–5인)

| 트랙 | 인력 | 주요 산출 |
|---|---|---|
| Backend Lead | 1 | Pet PATCH/DELETE·Calendar API·RQ 워커 통합·OpenAPI export |
| Backend Dev | 1 | Meals/Foods API·FatSecret factory·shared-types codegen·Devices API |
| Mobile Dev | 1 | Pet 편집·캘린더 주간뷰·식단 입력·홈 sparkline/도넛·푸시 등록 |
| AI/Infra | 1 | Caretail RealProvider·RQ 스케줄러·daily_health 집계·Caretail mock 14일 확장·푸시 알림 워커 |
| Lead/PM (5명일 때) | 1 | 키 발급 상태 추적·디스클레이머/문서 검수·시연 영상·W3 카드 분해 |

> 4명 운영 시 Lead/PM 역할을 Backend Lead 가 겸직, 시연 영상은 Mobile Dev 가 촬영.

---

## 7. File Map

```
apps/api/
  alembic/versions/0002_w2_models.py                      [new]
  alembic/versions/0003_daily_health.py                   [new]
  app/models/{meal,calendar_task,vet_visit,pet_food,
              notification_log,device,daily_health}.py    [new]
  app/models/pet.py                                       [edit: memo, allergies, photo_url, deleted_at]
  app/api/v1/pets.py                                      [edit: PATCH, DELETE]
  app/api/v1/meals.py                                     [new]
  app/api/v1/foods.py                                     [new]
  app/api/v1/calendar.py                                  [new]
  app/api/v1/health.py                                    [new]
  app/api/v1/devices.py                                   [new]
  app/integrations/health/real.py                         [edit: stub → 실 구현]
  app/integrations/health/mock.py                         [edit: 7→14일 확장]
  app/integrations/health/factory.py                      [edit: real swap]
  app/integrations/fatsecret/{__init__,mock,real,factory}.py  [new]
  app/integrations/push/{__init__,mock,expo,factory}.py   [new]
  app/workers/{__init__,queue,health_poll,scheduler,notifications}.py  [new]
  app/services/health_aggregate.py                        [new]
  seeds/pet_foods.py                                      [new]
  seeds/medical_baseline.py                               [new, W3 선행 시드]
  Dockerfile.worker                                       [new or edit]
  tests/test_pets.py                                      [edit: PATCH/DELETE 추가]
  tests/test_meals.py                                     [new]
  tests/test_foods.py                                     [new]
  tests/test_calendar.py                                  [new]
  tests/test_health_polling.py                            [new]
  tests/test_notifications.py                             [new]

apps/mobile/
  app/(tabs)/index.tsx                                    [edit: 홈 sparkline + 도넛]
  app/pets/[id]/index.tsx                                 [new]
  app/pets/[id]/edit.tsx                                  [new]
  app/pets/[id]/meal-new.tsx                              [new]
  app/calendar/index.tsx                                  [new]
  app/calendar/new.tsx                                    [new]
  src/api/{pets,meals,calendar,health,devices}.ts         [new or edit]
  src/components/{Sparkline,CalorieDonut}.tsx             [new]
  src/notifications/register.ts                           [new]

packages/shared-types/                                    [edit: meal/calendar/health 추가]

docs/
  w2-demo.md                                              [new]
  w2-retrospective.md                                     [new]
  data/pet-foods-source.md                                [new]
  spikes/caretail-spike.md                                [edit: W2 보강]
  api/openapi-w2.json                                     [generated]

.omc/plans/w3-ai-anomaly-budget-hospital.md               [new, Day 6~7 산출]
.omc/research/w2-demo.mp4                                 [new]

docker-compose.yml                                        [edit: worker 서비스]
```

---

## 8. Done Definition

- [ ] AC1~AC15 중 ≥ 12개 통과(목표 13~14).
- [ ] mypy 0 errors, ruff 0 errors, coverage ≥ 80% (AC14).
- [ ] shared-types codegen 적용, mobile typecheck 통과 (AC15).
- [ ] 90초 W2 시연 영상 1회.
- [ ] `.omc/plans/w3-ai-anomaly-budget-hospital.md` 초안 존재.
- [ ] `docs/w2-retrospective.md` 작성.
- [ ] CI green (`.github/workflows/api.yml`).

---

## 9. Open Questions

1. Caretail 키가 W2 끝(5.14)에도 미발급일 경우 W3 진입 시 어떻게? — 현재 가정: 발급됨. 미발급 시 W3 anomaly 모델은 mock 14일 시드만으로 학습 가능한 룰 기반 + IsolationForest 경로 우선, 실 데이터 검증은 W4로 이월.
2. FatSecret 펫 사료 데이터가 빈약할 가능성 — 자체 펫 사료 DB 200건 시드를 *항상 우선*으로 정렬. 200건 시드 출처 검증을 누구(lead) 가 언제까지(Day 2 EOD) 끝낼지 확정 필요. [추정] 브랜드별 공식 사이트 + 펫푸드 수입사 카탈로그 1차.
3. mypy strict 수준 — basic vs strict. W1에서 strict 동결했으므로 W2도 strict 유지 권장. `[strict-optional]`, `disallow-any-generics` 까지 켜되 `disallow-untyped-decorators` 는 일부 FastAPI 데코레이터 호환을 위해 완화 검토.
4. 푸시 알림 quiet hours 사용자 설정 — W2는 hard-coded(22~07), 정식 설정은 W3 사용자 프로필 화면과 함께. 본선까지 immediate 푸시는 quiet hours 무시 옵션 제공할지 결정.
5. 캘린더 RRULE(반복 일정) 지원 — W2는 단일 due_at 만, RRULE은 W3 또는 본선. spec auth-and-family § 미정.
6. EAS Build dev client 빌드 — Day 5 푸시 토큰 발급을 위해 W2 중 1회 필요할 수 있음. 빌드 시간 ~30분 + 인증서 셋업 시간 [추정 1~2h] 별도 확보.

---

## 10. Changelog

- 2026-05-03 — 초안 작성. W1 산출물(인증/가족/Pet/MockHealthProvider 14일/shared-types codegen) 가정. Caretail/FatSecret 키 발급 가정하되 mock 자동 폴백 유지. mypy 0 errors Day 6 회복.
