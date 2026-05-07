# W2 Plan · Pet/Health/Nutrition CRUD + 헬스 폴링 (v2 — 스코프 피벗 반영)

> **파생 plan**: jazzy-roaming-rose.md (스코프 피벗 SOT)

이 plan 은 2026-05-06 스코프 피벗 후 v2. 카메라/오디오 입력은 W3-v2 에서 다룸. 워치(Caretail) 통합은 옵셔널로 강등되어 폴링은 기본 비활성. 식이 관리 모델은 사료 종류 메타가 진단 입력으로 합류하기 위한 food_kind 필드 추가.

**2026-05-07 추가 결정**: Caretail 워치 통합은 옵셔널 모드에서 **완전 제거**로 변경. 트랙 A 의 Caretail RealProvider stub + 폴링 워커 작업은 본 plan 에서 out of scope. AC9–AC11, AC16 모두 삭제.

> 기간: 2026-05-08(금) ~ 2026-05-14(목), 7일 · 4–5인 팀
> 상위 plan: `~/.claude/plans/jazzy-roaming-rose.md` (피벗 SOT) / `~/.claude/plans/ai-compressed-codd.md` § 10 W2 / `docs/specs/02-health-analysis.md` § 2~3 / `docs/specs/05-medical-budget-savings.md` § 2~3
> 모드: W1과 동일하게 mock-first 유지하되 FatSecret 키 발급 시 즉시 swap. W1 freeze 해제 후 mypy 0 errors 회복 의무.

---

## 1. Requirements Summary

W2 종료(5.14) 시점에 **Pet·Family·일정 CRUD 풀**, **FatSecret 영양 입력**, **모바일 홈 화면(sparkline·칼로리)**, **푸시 알림 기본 동작**이 mock-first로 동작해야 한다. W1에서 동결한 mypy strict는 0 errors 회복하고, shared-types codegen 적용을 모바일 영양·일정 화면까지 확대한다. 모든 외부 통합은 W1과 동일하게 Provider 추상 + factory 패턴으로 swap-ready 상태를 유지한다. **Caretail 워치 통합은 2026-05-07 결정으로 완전 제거** — Caretail OAuth, 폴링 워커, RQ health_poll 큐 모두 out of scope. 식이 모델에 `food_kind` 필드가 추가되어 사료 종류 메타가 W3-v2 진단 입력으로 합류하는 첫 단계를 마련한다.

### 1.1 In Scope

- `Pet` 모델 확장(메모, 알러지, photo_url) + `PATCH /v1/pets/{id}`, `DELETE /v1/pets/{id}` 풀 구현 + 가족 권한 검증.
- `Meal`, `CalendarTask`, `VetVisit` 3개 신규 모델 + `0002_w2_models` Alembic 마이그레이션. `Meal` 모델에 `food_kind: Enum('사료', '간식', '일반식', '처방식')` 컬럼 포함.
- `POST/GET /v1/pets/{id}/meals`, `GET /v1/pets/{id}/meals/today` (FatSecret API + 자체 펫 사료 DB 시드 200건). `food_kind` 저장·반환 포함.
- `GET/POST/PATCH/DELETE /v1/calendar` (일정 CRUD + assignee 위임 + 완료 체크 + 가족 단위 조회).
- RQ 워커 + scheduler(`apps/api/app/workers/notifications.py`) — notifications 큐. `HealthSnapshot` upsert + `daily_health` 일일 집계 (MockHealthProvider 14일 시드 기반).
- `POST /v1/pets/{id}/health/sync` (수동 트리거) + `GET /v1/pets/{id}/health/snapshots` + `GET /v1/pets/{id}/health/daily` 실 응답.
- 푸시 알림 기본: Expo Notifications 연동 + `device_token` 등록 엔드포인트 + `notify_health_event` worker 함수(룰 기반 트리거: 이상 진단 결과 발생 시 알림).
- 모바일 홈 화면: 활동/심박 7일 sparkline + 식단 칼로리 도넛 차트 + 빠른 식단 입력 모달.
- 모바일: Pet 편집/삭제 화면, 캘린더 주간 뷰, 식단 입력(검색 → 양 입력 → 저장).
- mypy 0 errors 회복(W1 freeze 해제) + ruff strict + coverage 80%+ 유지.
- shared-types codegen 적용 확대: meal/calendar/health 스키마까지.
- W3-v2 카드 분해(`.omc/plans/w3-v2-multimodal-diagnosis-hospital.md`) 초안 — Day 7 산출물.

### 1.2 Out of Scope (W3-v2 이후)

- AI 헬스 분석 이미지/오디오 입력 (카메라·음성 기반 질병 의심 분류) — W3-v2.
- Stage 2 질병 후보 LM, `/infer/disease` 로컬 AI 서버 mTLS 통신 — W3-v2~W4-v2.
- 의료비 예측식·`MedicalBudget` 모델·`/v1/budget` — 본선 보류.
- 병원 매칭(공공데이터 동물병원 ETL + 카카오맵) + `/v1/hospitals` — W3-v2.
- 적금 권장 카드, 외부 가입 딥링크, 후원 결합 — 본선 보류.
- 실 결제·오픈뱅킹 직접 연동 — Out (시연 범위 외).
- Caretail 워치 통합 일체 — 2026-05-07 결정으로 완전 제거. `HealthProvider`/`MockHealthProvider`/`HealthSnapshot` 코드 자산은 W3-v2 이미지/오디오 진단 저장용으로 재활용.

### 1.3 Constraints

- W1 가정 유지: 카카오 키는 발급됨. Caretail 통합은 2026-05-07 완전 제거 결정으로 해당 없음.
- 4–5인 팀 분담 그대로(백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1). 5.10 일요일은 작업 가능, 5.13 수요일은 mypy 회복 데이로 신규 코드 동결.
- Day 7(5.14)은 freeze + 통합 + W3-v2 카드 + 시연 영상 갱신 전용. 신규 코드 금지.
- 의료/금융 디스클레이머는 W2 단계에서 *알림 본문·식단 추천 카드*에 이미 노출되어야 함(spec 05 § 10).

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `alembic upgrade head` 실행 시 `meal`, `calendar_task`, `vet_visit` 3개 테이블 + `pet` 테이블 컬럼 확장(memo, allergies jsonb, photo_url) 반영. `meal` 테이블에 `food_kind` 컬럼(`사료`/`간식`/`일반식`/`처방식` Enum) 포함 | `psql -c "\dt"` 및 `\d meal` 출력 검증 |
| AC2 | `PATCH /v1/pets/{id}` 가 owner/member 모두 200, 다른 가족 사용자는 404 | `pytest apps/api/tests/test_pets.py::test_pet_patch_rbac` |
| AC3 | `DELETE /v1/pets/{id}` 는 owner 만 204, member 는 403 `FORBIDDEN` | `pytest ::test_pet_delete_owner_only` |
| AC4 | `POST /v1/pets/{id}/meals` 가 mock FatSecret 응답을 받아 `Meal{kcal, protein_g, carbs_g, fat_g, food_kind}` 정상 저장하고, `GET /v1/pets/{id}/meals` 응답에 `food_kind` 포함 | `pytest apps/api/tests/test_meals.py::test_meal_create_with_mock_fatsecret` |
| AC5 | `GET /v1/pets/{id}/meals/today` 가 당일(KST) 칼로리 합·매크로 합 반환, 비어 있을 때 0 | `pytest ::test_meals_today_aggregate` |
| AC6 | 자체 펫 사료 DB 시드 200건이 `seed_pet_foods.py` 로 적재되고 `GET /v1/foods/search?q=로얄캐닌` 가 ≥ 1건 반환 | `pytest apps/api/tests/test_foods.py::test_pet_food_search` |
| AC7 | `POST /v1/calendar` 로 task 생성 후 `GET /v1/calendar?from=&to=` 가 가족 멤버 모두에게 동일 응답 | `pytest apps/api/tests/test_calendar.py::test_calendar_family_visibility` |
| AC8 | `PATCH /v1/calendar/{id}` 로 assignee 위임 + `done=true` 체크 시 `completed_at` UTC 기록 | `pytest ::test_calendar_assign_and_complete` |
| AC9 | Mobile 홈 화면에서 7일 활동 sparkline + 심박 sparkline + 칼로리 도넛(오늘) 동시 렌더 — 시연 영상 30초 | `.omc/research/w2-demo.mp4` 첨부, `docs/w2-demo.md` |
| AC10 | Mobile 식단 입력: 음식 검색 → 양 입력 → 저장 → 홈 칼로리 즉시 갱신 | 시연 영상 동일 회차 |
| AC11 | `mypy app` 0 errors (W1 strict freeze 해제), `ruff check .` 0 errors, `pytest --cov=app --cov-fail-under=80` 통과 | CI 로그 (`.github/workflows/api.yml`) green |
| AC12 | `packages/shared-types/` 가 W2 신규 스키마(meal, calendar_task, health_snapshot, daily_health)까지 포함하여 codegen 후 mobile 빌드 통과 | `pnpm -C apps/mobile typecheck` 0 errors |

> Done 임계: **12개 필수 AC 중 ≥ 9개 통과** (AC9–AC11 은 Caretail 삭제로 제거됨, AC16 삭제. 2026-05-07 결정). 미통과는 W3-v2 첫날 보강 카드.

---

## 3. Implementation Steps (Day 단위)

### 3.1 Day 1 (5.8 금) — RQ 워커 셋업 + FatSecret Mock

> W1 freeze 해제. mock-first 유지.

#### 트랙 A

> **2026-05-07 결정으로 트랙 A 전체 삭제**. Caretail 워치 통합은 본 프로젝트에서 out of scope. `apps/api/app/integrations/health/` 의 `HealthProvider` Protocol + `MockHealthProvider` + `HealthSnapshot` 모델은 W3-v2 의 이미지/오디오 진단 데이터 저장용으로 재활용 (s3_ref 컬럼 추가). Caretail-specific 환경변수 (`CARETAIL_*`) 와 폴링 워커는 삭제.

#### 트랙 B · RQ 워커 + 스케줄러 셋업 (backend lead)
- [ ] `apps/api/app/workers/__init__.py` + `apps/api/app/workers/queue.py` — RQ Queue("notifications") 정의, `redis_url=settings.redis_url`.
- [ ] `apps/api/app/workers/health_poll.py` — `def poll_pet_health(pet_id: UUID) -> int`:
  - factory → provider.fetch_window(since=last_ingest_ts)
  - HealthSnapshot upsert (pk=pet_id+ts), `daily_health` rollup 함수 호출.
  - 반환: 새로 적재된 row 수.
- [ ] `apps/api/app/workers/scheduler.py` — notifications 큐 워커. 워커 자체는 W3-v2 의 notifications 큐 (`notify_health_event`) 용으로 유지. `health_poll` 큐 + Caretail 폴링은 삭제.
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
- [ ] `apps/api/app/models/meal.py` 신규: `Meal(id, pet_id FK, ts, source enum('fatsecret','custom','seed'), food_id, food_name, qty_g, kcal, protein_g, carbs_g, fat_g, note, food_kind enum('사료','간식','일반식','처방식'))`. `food_kind` 는 식이↔건강 연결의 첫 단계로 W3-v2 진단 입력 메타로 활용됨.
- [ ] `apps/api/app/models/calendar_task.py` 신규: `CalendarTask(id, family_id FK, pet_id FK nullable, title, kind enum('meal','walk','medicine','vet','custom'), due_at, assignee_id FK→user, created_by FK, completed_at, notes)`.
- [ ] `apps/api/app/models/vet_visit.py` 신규: `VetVisit(id, pet_id FK, visited_at, hospital_name, reason, cost_krw, attachments jsonb)` — W2는 모델만, CRUD는 W3-v2.
- [ ] `apps/api/app/models/pet_food.py` 신규: `PetFood(id, brand, name, kcal_per_100g, protein, carbs, fat, source enum('seed','fatsecret','user'))`.
- [ ] `apps/api/app/models/notification_log.py` 신규: `NotificationLog(id, user_id, pet_id, kind, payload jsonb, sent_at, channel enum('expo','log'))`.
- [ ] `apps/api/app/models/device.py` 신규: `Device(id, user_id, expo_token unique, platform enum, last_seen_at)`.
- [ ] `alembic revision --autogenerate -m "0002_w2_models"` → 검증 → commit (AC1). 마이그레이션에 `food_kind` 컬럼 포함 확인.

**Day 1 종료 조건**: AC1 통과 (`meal.food_kind` 컬럼 포함). 워커 컨테이너가 `redis-cli LPUSH` 받은 dummy job 1개를 소화하는 것까지 확인.

---

### 3.2 Day 2 (5.9 토) — Pets PATCH/DELETE + Meals POST/GET

#### 트랙 A · `/v1/pets` PATCH/DELETE (backend lead)
- [ ] `apps/api/app/api/v1/pets.py` 에 `PATCH /{id}`, `DELETE /{id}` 추가.
  - PATCH: 가족 멤버(member 이상) → 부분 업데이트(memo, allergies, weight, neutered, photo_url, conditions).
  - DELETE: **owner 전용** → soft delete(`deleted_at` 컬럼) — Pet 모델에 `deleted_at` 추가, 기존 GET/PATCH는 자동 필터.
- [ ] `apps/api/tests/test_pets.py` — AC2/AC3 + 마지막 펫 삭제 시 family 단위 스냅샷 보존 검증.

#### 트랙 B · Meals API (backend dev)
- [ ] `apps/api/app/api/v1/meals.py` 신규:
  - `POST /v1/pets/{pet_id}/meals` — body `{food_id?, food_name?, qty_g, ts?, food_kind?}`. food_id 없으면 FatSecret search 후 매칭, 매칭 실패 시 custom kcal 직접 입력 허용. `food_kind` 저장.
  - `GET /v1/pets/{pet_id}/meals?from&to` — 페이지네이션. `food_kind` 포함 반환.
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

**Day 2 종료 조건**: AC2~AC6 통과. AC4 에서 `food_kind` 저장·반환 확인 포함.

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

#### 트랙 D · W3-v2 선행 조사 (AI/infra)
- [ ] `docs/spikes/` 에 이미지/오디오 데이터셋 라이선스 사전 조사 메모 추가 (W3-v2 Day 1 준비).

**Day 3 종료 조건**: AC7, AC8 통과. mobile 캘린더 화면에서 task 생성·완료가 시각적으로 동작.

---

### 3.4 Day 4 (5.11 월) — health 엔드포인트 + daily_health 집계

#### 트랙 A · health 엔드포인트 + 워커 통합 (backend lead + AI/infra)
- [ ] `apps/api/app/api/v1/health.py` 신규:
  - `POST /v1/pets/{id}/health/sync` — RQ enqueue, `{job_id}` 202.
  - `GET /v1/pets/{id}/health/snapshots?since=` — 최신 200개 또는 since 이후.
  - `GET /v1/pets/{id}/health/daily?from=&to=` — `daily_health` 집계 응답.
- [ ] `apps/api/app/services/health_aggregate.py` — `rollup_daily(pet_id, date)` 함수: 스냅샷 → 일일 활동 분 합/심박 평균/수면 deep ratio/체중 last.
- [ ] `apps/api/app/models/daily_health.py` 신규 + Alembic `0003_daily_health`.
- [ ] `apps/api/tests/test_health_polling.py` — fakeredis + RQ `SimpleWorker(burst=True)` 경로 검증.

#### 트랙 B · MockHealthProvider 14일 시드 보강 (AI/infra)
- [ ] `apps/api/app/integrations/health/mock.py` — 7일 → 14일 확장 (W1 베이스). anomaly 시그널을 day 12~14 활동 30%↓, 심박 평균 10%↑ 패턴으로 결정적 생성(W3-v2 이미지/오디오 진단 입력 검증용).

#### 트랙 C · shared-types codegen 확대 (backend dev)
- [ ] `packages/shared-types/openapi.ts` 재생성 — meal/calendar/health 스키마 포함. `food_kind` enum 포함 확인.
- [ ] `apps/mobile/src/api/types.ts` 가 shared-types import 하도록 정리 (AC12).

**Day 4 종료 조건**: health 엔드포인트 통합 테스트 통과. MockHealthProvider 14일 시드 데이터 렌더 확인.

---

### 3.5 Day 5 (5.12 화) — Mobile 홈 sparkline + 칼로리 차트 + 알림

#### 트랙 A · 푸시 알림 인프라 (backend dev + mobile dev)
- [ ] `apps/api/app/api/v1/devices.py` — `POST /v1/devices {expo_token, platform}`.
- [ ] `apps/api/app/integrations/push/__init__.py` PushProvider Protocol.
- [ ] `apps/api/app/integrations/push/{mock,expo,factory}.py` — Expo Push API client.
- [ ] `apps/api/app/workers/notifications.py` — `notify_health_event(pet_id, kind, payload)`, 룰 트리거: 이상 진단 결과 발생 시 푸시 알림.
- [ ] `apps/api/tests/test_notifications.py` — 푸시 알림 워커 happy-path 검증.
- [ ] `apps/mobile/src/notifications/register.ts` — Expo Notifications permission 요청 + 토큰 등록 호출 + 백그라운드 핸들러.

#### 트랙 B · Mobile 홈 화면 (mobile dev)
- [ ] `apps/mobile/app/(tabs)/index.tsx` — 펫 셀렉터 + 7일 활동 sparkline + 7일 심박 sparkline + 오늘 칼로리 도넛(목표 대비) + 다음 일정 카드 + 빠른 식단/산책 입력 FAB.
- [ ] `apps/mobile/src/components/Sparkline.tsx` — `react-native-svg` 기반 [추정 — KakaoMap spike에서 같은 라이브러리 채택했다면 재사용].
- [ ] `apps/mobile/src/components/CalorieDonut.tsx`.
- [ ] 디스클레이머 텍스트: "참고용 추정치, 의료 진단 아님" 카드 푸터(spec 02 § 7, spec 05 § 10 의무).

#### 트랙 C · 의료비 통계 베이스라인 시드 *준비* (AI/infra, W3-v2 선행)
- [ ] `apps/api/seeds/medical_baseline.py` — 품종·나이대 12 슬롯 × p50/p90 정적 테이블 시드 작성(KB펫금융보고서 등 출처 표기).
- [ ] **본 W2 In Scope 아님**(spec 05 § 8 W1 산출이지만 W1에서 누락된 경우만 W2로 이월). W3-v2 예측식 코드는 작성하지 않음.

**Day 5 종료 조건**: AC9, AC10 통과. 모바일 홈에서 sparkline·도넛·일정 카드 동시 렌더 + 푸시 알림 1건 수신.

---

### 3.6 Day 6 (5.13 수) — mypy 0 errors 회복 + shared-types 적용 확대 + W3-v2 카드 분해

> **신규 기능 코드 동결**. 타입·문서·테스트·차주 카드.

- [ ] `mypy app` 0 errors 회복(AC11).
  - W1 freeze 동안 누적된 `# type: ignore` 제거 우선순위 리스트 작성 → 반나절 정리.
  - `from __future__ import annotations` 일관 적용, Pydantic v2 `model_validate` 마이그레이션 잔여 정리.
- [ ] `ruff check . --fix` 후 잔여 violation 수동 정리.
- [ ] `pytest --cov-fail-under=80` 통과 확인. 부족 시 빈 곳에 happy-path 테스트 추가.
- [ ] `packages/shared-types` codegen 실행 + mobile typecheck 통과(AC12).
- [ ] `.omc/plans/w3-v2-multimodal-diagnosis-hospital.md` 초안 — 이미지 진단 + 오디오 진단 + 병원 매칭을 9~10일 일정으로 분배 (5.15~5.21 W3-v2 + 5.22~5.24 finalize 전 마지막 통합). 피벗 SOT(`jazzy-roaming-rose.md`) § W3 트랙 분담 참조.

---

### 3.7 Day 7 (5.14 목) — Freeze · 통합 · 시연 영상 갱신

- [ ] AC1~AC12 점검표 갱신. 필수 AC(AC1~AC12) ≥ 9 확인.
- [ ] `docs/w2-retrospective.md` — 잘 된 것/막힌 것/W3-v2 이월. Caretail 완전 제거 결정(2026-05-07) 기록 포함.
- [ ] OpenAPI export → `docs/api/openapi-w2.json`. `food_kind` 필드 포함 확인.
- [ ] 시연 영상 갱신 — W1 demo + W2 흐름(로그인 → 가족 → 펫 → 식단 입력(`food_kind` 선택 포함) → 캘린더 → 홈 sparkline → 알림 수신) 90초.
- [ ] `.omc/research/api-applications/` FatSecret 키 발급 상태 스냅샷 갱신.

---

## 4. Risks & Mitigations

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | Caretail 워치 통합 — **2026-05-07 완전 제거 결정으로 이 위험 항목 해소**. `HealthProvider` Protocol + `MockHealthProvider` + `HealthSnapshot` 모델은 W3-v2 이미지/오디오 진단 데이터 저장용으로 재활용. | N/A | N/A | 해소됨 |
| R2 | FatSecret OAuth1 승인 지연 | 高 | 中 | 자체 펫 사료 DB 200건 시드 우선순위 상승, FatSecret은 mock으로 W2 종료까지 운영 가능. AC4는 mock fixture로 통과. |
| R3 | RQ 워커가 dev 머신에서 `redis://localhost:6379` 외 환경에서 실패 | 中 | 中 | `docker compose up worker` 표준화, fakeredis 테스트 픽스처, README에 redis URL env 명시. |
| R4 | mypy 0 errors 회복이 Day 6 하루로 부족 | 中 | 中 | Day 1~5 동안 새 코드는 처음부터 strict 통과 룰 적용(PR checker). Day 6은 *잔여*만 정리. 부족 시 일부 모듈 `[strict-optional]` 한정 완화 + W3-v2로 잔여 이월. |
| R5 | Expo push token 발급이 Expo Go 환경에서 제한 | 中 | 低 | EAS Build dev client 1회 빌드(W1 KakaoMap과 합쳐 진행), 실패 시 시연은 mock provider + `notification_log` 행으로 대체. |
| R6 | 캘린더 권한 체크 누락으로 cross-family 일정 노출 | 低 | 高 | `require_family` 의존 + cross-family 차단 테스트 명시(AC7), code review 필수. |
| R7 | shared-types codegen이 Pet/Meal 순환 참조 발생 | 低 | 中 | OpenAPI tag 분리 + `$ref` 유지, 실패 시 type alias 수동 패치 + W3-v2에 자동화 재시도. `food_kind` enum 타입 포함 여부 확인. |
| R8 | 5.10 일요일·5.13 수요일 인력 부재 | 中 | 中 | Day 3(일)은 캘린더 단일 트랙 위주로 부담 분산, Day 6(수)은 동결로 비동기 작업 가능. |
| R9 | 푸시 quiet hours 미구현 상태에서 한밤 알림 발송 | 低 | 中 | W2는 quiet hours 임시 hard-coded(22~07 차단), 정식 사용자 설정은 W3-v2로 명시 이월. |
| R10 | 워커가 동일 pet_id 동시 enqueue로 race 발생 | 低 | 中 | RQ `Job.id=f"poll:{pet_id}:{slot}"` 5분 슬롯 dedup, upsert로 중복 안전. |
| R11 | `food_kind` 값이 FatSecret 검색 결과에 없어 null 다수 | 中 | 低 | `food_kind` 는 nullable 허용, 미입력 시 UI에서 사용자가 직접 선택. 시드 200건에는 모두 명시. |

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
mypy app                       # 0 errors 회복(AC11)
cd ../../packages/shared-types
pnpm codegen
cd ../../apps/mobile
pnpm typecheck                 # AC12
```

### 5.2 수동 (AC9, AC10)
1. `pnpm -C apps/mobile start` → 로그인(mock) → 가족 → 펫 선택.
2. 식단 입력 → `food_kind` 선택(사료/간식/일반식/처방식) → 칼로리 도넛 즉시 갱신.
3. 캘린더 → 산책 task 생성 → 가족 다른 계정 로그인에서 보임.
4. `POST /v1/pets/{id}/health/sync` → 30초 후 홈 sparkline 14일 데이터 표시.
5. 푸시 알림 1건 수신(테스트용 trigger).
6. 90초 시연 영상 → `.omc/research/w2-demo.mp4`.

### 5.3 종료 점검 (Day 7 PM)
- 필수 AC 통과 < 9 → W3-v2 첫날 보강 카드 삽입.
- mypy 0 errors 미달 시 W3-v2 첫날 보강.

---

## 6. Team Allocation (4–5인)

| 트랙 | 인력 | 주요 산출 |
|---|---|---|
| Backend Lead | 1 | Pet PATCH/DELETE·Calendar API·RQ 워커 통합·health 엔드포인트·OpenAPI export |
| Backend Dev | 1 | Meals/Foods API(`food_kind` 포함)·FatSecret factory·shared-types codegen·Devices API |
| Mobile Dev | 1 | Pet 편집·캘린더 주간뷰·식단 입력(`food_kind` 선택 UI)·홈 sparkline/도넛·푸시 등록 |
| AI/Infra | 1 | MockHealthProvider 14일 시드 확장·RQ 스케줄러·daily_health 집계·푸시 알림 워커·W3-v2 데이터셋 사전 조사 |
| Lead/PM (5명일 때) | 1 | 디스클레이머/문서 검수·시연 영상·W3-v2 카드 분해·FatSecret 키 발급 상태 추적 |

> 4명 운영 시 Lead/PM 역할을 Backend Lead 가 겸직, 시연 영상은 Mobile Dev 가 촬영.

---

## 7. File Map

```
apps/api/
  alembic/versions/0002_w2_models.py                      [new — meal.food_kind 컬럼 포함]
  alembic/versions/0003_daily_health.py                   [new]
  app/models/{meal,calendar_task,vet_visit,pet_food,
              notification_log,device,daily_health}.py    [new — meal.py 에 food_kind 필드 포함]
  app/models/pet.py                                       [edit: memo, allergies, photo_url, deleted_at]
  app/api/v1/pets.py                                      [edit: PATCH, DELETE]
  app/api/v1/meals.py                                     [new — food_kind 저장·반환]
  app/api/v1/foods.py                                     [new]
  app/api/v1/calendar.py                                  [new]
  app/api/v1/health.py                                    [new]
  app/api/v1/devices.py                                   [new]
  app/integrations/health/mock.py                         [edit: 7→14일 확장, W3-v2 이미지/오디오 진단 저장용 재활용]
  app/integrations/fatsecret/{__init__,mock,real,factory}.py  [new]
  app/integrations/push/{__init__,mock,expo,factory}.py   [new]
  app/workers/{__init__,queue,scheduler,notifications}.py  [new — health_poll 큐 삭제, notifications 큐 유지]
  app/services/health_aggregate.py                        [new]
  seeds/pet_foods.py                                      [new]
  seeds/medical_baseline.py                               [new, W3-v2 선행 시드]
  Dockerfile.worker                                       [new or edit]
  tests/test_pets.py                                      [edit: PATCH/DELETE 추가]
  tests/test_meals.py                                     [new — food_kind AC4 포함]
  tests/test_foods.py                                     [new]
  tests/test_calendar.py                                  [new]
  tests/test_health_polling.py                            [new — health 엔드포인트 + daily_health 집계]
  tests/test_notifications.py                             [new — 푸시 알림 워커]

apps/mobile/
  app/(tabs)/index.tsx                                    [edit: 홈 sparkline + 도넛]
  app/pets/[id]/index.tsx                                 [new]
  app/pets/[id]/edit.tsx                                  [new]
  app/pets/[id]/meal-new.tsx                              [new — food_kind 선택 UI]
  app/calendar/index.tsx                                  [new]
  app/calendar/new.tsx                                    [new]
  src/api/{pets,meals,calendar,health,devices}.ts         [new or edit]
  src/components/{Sparkline,CalorieDonut}.tsx             [new]
  src/notifications/register.ts                           [new]

packages/shared-types/                                    [edit: meal/calendar/health + food_kind enum 추가]

docs/
  w2-demo.md                                              [new]
  w2-retrospective.md                                     [new — Caretail 완전 제거 결정(2026-05-07) 기록]
  data/pet-foods-source.md                                [new]
  api/openapi-w2.json                                     [generated — food_kind 포함]

.omc/plans/w3-v2-multimodal-diagnosis-hospital.md         [new, Day 6~7 산출]
.omc/research/w2-demo.mp4                                 [new]

docker-compose.yml                                        [edit: worker 서비스]
```

---

## 8. Done Definition

- [ ] 필수 AC(AC1~AC12) 중 ≥ 9개 통과(목표 10~12).
- [ ] mypy 0 errors, ruff 0 errors, coverage ≥ 80% (AC11).
- [ ] shared-types codegen 적용, mobile typecheck 통과 (AC12).
- [ ] `Meal.food_kind` 컬럼이 마이그레이션·API·codegen 모두에 반영.
- [ ] 90초 W2 시연 영상 1회.
- [ ] `.omc/plans/w3-v2-multimodal-diagnosis-hospital.md` 초안 존재.
- [ ] `docs/w2-retrospective.md` 작성 (Caretail 완전 제거 결정 기록 포함).
- [ ] CI green (`.github/workflows/api.yml`).

---

## 9. Open Questions

1. FatSecret 펫 사료 데이터가 빈약할 가능성 — 자체 펫 사료 DB 200건 시드를 *항상 우선*으로 정렬. 200건 시드 출처 검증을 누구(lead) 가 언제까지(Day 2 EOD) 끝낼지 확정 필요.
2. mypy strict 수준 — basic vs strict. W1에서 strict 동결했으므로 W2도 strict 유지 권장. `[strict-optional]`, `disallow-any-generics` 까지 켜되 `disallow-untyped-decorators` 는 일부 FastAPI 데코레이터 호환을 위해 완화 검토.
3. 푸시 알림 quiet hours 사용자 설정 — W2는 hard-coded(22~07), 정식 설정은 W3-v2 사용자 프로필 화면과 함께. 본선까지 immediate 푸시는 quiet hours 무시 옵션 제공할지 결정.
4. 캘린더 RRULE(반복 일정) 지원 — W2는 단일 due_at 만, RRULE은 W3-v2 또는 본선.
5. EAS Build dev client 빌드 — Day 5 푸시 토큰 발급을 위해 W2 중 1회 필요할 수 있음. 빌드 시간 ~30분 + 인증서 셋업 시간 [추정 1~2h] 별도 확보.
6. `food_kind` 기본값 — 미입력 시 `null` 허용 vs `일반식` 자동 fallback. UI 에서 필수/선택 여부 결정 필요. W3-v2 진단 입력 메타에서 null 처리 방식 확정 전까지 nullable 유지 권장.
7. `CARETAIL_*` 환경변수 `.env` 처리 — 완전 제거 아닌 deprecated 주석으로 남겨 follow-up. `.omc/plans/open-questions.md` 업데이트 필요.

---

## 10. Changelog

- 2026-05-03 — 초안 작성. W1 산출물(인증/가족/Pet/MockHealthProvider 14일/shared-types codegen) 가정. Caretail/FatSecret 키 발급 가정하되 mock 자동 폴백 유지. mypy 0 errors Day 6 회복.
- 2026-05-06 — **v2 피벗 반영** (jazzy-roaming-rose.md SOT). Caretail 폴링 옵셔널 강등(`CARETAIL_POLLING_ENABLED=false` 기본), AC9–AC11 임계 제외, AC16 추가. `Meal.food_kind` 필드 추가(사료↔건강 연결 첫 단계, W3-v2 진단 입력 메타). W3 참조를 W3-v2 로 업데이트.
- 2026-05-07 — **Caretail 워치 통합 완전 제거**. 트랙 A(RealProvider stub) 삭제, AC9–AC11·AC16 삭제, AC 재번호 (구 AC12→AC9, AC13→AC10, AC14→AC11, AC15→AC12). Done 임계 12개 중 ≥ 9개. `HealthProvider`/`MockHealthProvider`/`HealthSnapshot` 코드 자산은 W3-v2 이미지/오디오 진단 저장용으로 재활용. `CARETAIL_*` 환경변수는 deprecated 주석으로 보존(follow-up).
