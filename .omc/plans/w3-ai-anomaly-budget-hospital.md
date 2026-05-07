# W3 Plan · Stage 1 Anomaly + 의료비 예측 + 동물병원 매칭

> 기간: 2026-05-15(금) ~ 2026-05-21(목), 7일 · 4–5인 팀
> 상위 plan: `~/.claude/plans/ai-compressed-codd.md` § 10 W3 / `docs/specs/02-health-analysis.md` § 3 / `docs/specs/05-medical-budget-savings.md` § 2 / `docs/spikes/external-apis.md` § 3 / `docs/spikes/kakao-map-spike.md`
> 모드: W2와 동일하게 mock-first 유지. 로컬 AI 서버(RTX 5090) 도입 첫 주차이지만 Cloudflare Tunnel 두절·키 부재 시 룰 기반 fallback 자동 동작. Stage 2 LM·적금 권장 카드·후원·시연 영상은 W4로 이월.

---

## 1. Requirements Summary

W3 종료(5.21) 시점에 **Stage 1 anomaly 추론 (로컬 AI 서버 + 클라우드 API 호출)**, **의료비 예측식 + MedicalBudget CRUD**, **베이스라인 통계 시드 30+ 셀**, **공공데이터 동물병원 ETL + PostGIS 근접 검색 + KakaoMap WebView 마커**, **모바일 홈 의료비 카드 + 병원 리스트/지도 + 마커 탭→상세** 가 mock-first로 동작해야 한다. Stage 2 질병 분류 LM은 W4 산출이므로, W3 의료비 예측식의 disease term은 mock prob=0 으로 단락(short-circuit)하고 anomaly term + 기저질환 가산만으로 p50/p90 + bootstrap CI를 계산한다. 모든 외부 통합(Caretail/FatSecret/data.go.kr)은 W1·W2 와 동일하게 Provider 추상 + factory 패턴을 유지하고, 키 부재 시 fixture 기반 mock 으로 자동 폴백한다. mypy strict, ruff strict, pytest coverage ≥ 80% 는 W2 회복 수준에서 유지한다.

### 1.1 In Scope

- 로컬 AI 서버 (`apps/ai-server`) 신규: FastAPI + scikit-learn(IsolationForest) + numpy(rolling z-score), `POST /infer/anomaly` 엔드포인트.
- Anomaly 입력 어댑터: 직전 14일 `daily_health` (활동 분, 평균 심박, 수면 deep ratio, 체중 변화율) → feature vector.
- Anomaly 모델: IsolationForest(contamination=0.1, n_estimators=100) + univariate rolling z-score 앙상블 → `score ∈ [0,1]` (sigmoid 정규화) + 기여 feature top-3.
- 클라우드 API → 로컬 AI 서버 통신: mTLS + `AI_SERVER_SHARED_SECRET` HMAC-SHA256 헤더 (`X-AISERVER-SIG`), 5초 타임아웃, 실패 시 룰 기반 fallback(`apps/api/app/services/anomaly_fallback.py`).
- `apps/api/app/integrations/aiserver/{__init__,client,fallback,factory}.py` — `AnomalyProvider` Protocol + Real/Mock/Fallback 3종.
- `Diagnosis` 모델 신규(spec 02 § 3.3) + Alembic `0004_diagnosis_anomaly`. W3는 `top_diseases=[]`, `action`은 임계 기반 결정(score≥0.7 immediate, 0.4~0.7 schedule, <0.4 observe).
- `POST /v1/pets/{id}/health/analyze` — 직전 14일 daily_health 조회 → AI 서버 호출 → Diagnosis 저장 → MedicalBudget recompute 트리거 → `{diagnosis_id, anomaly_score, action, budget_id}` 반환.
- 의료비 예측식(spec 05 § 2.3, MVP 해석가능형):
  - `base = breed_age_baseline.{p50|p90}` (베이스라인 시드 룩업)
  - `risk_multiplier = 1 + α·anomaly + β·Σ(disease_prob × disease_cost_factor) + γ·chronic_factor`
  - W3는 disease term=0 (β·Σ=0), `α=0.6`, `γ=0.2 per chronic condition`(상한 0.6)으로 시작 — `apps/api/app/services/budget_predict.py` 모듈에 상수 분리.
  - Bootstrap n=1000 → p50/p90/CI(90%) 산출 (numpy 의존).
- `MedicalBudget` 모델(spec 05 § 2.4) + Alembic `0005_medical_budget`.
- `GET /v1/pets/{id}/budget` (최신 1건) + `POST /v1/pets/{id}/budget/recompute` (강제 재계산, 가족 멤버 권한).
- 베이스라인 통계 시드: `apps/api/seeds/medical_baseline.py` — **30+ 셀** (xs/sm/md/lg × puppy/adult/senior × 3 baseline range, 출처 KB펫금융보고서·통계청·학회 자료, `docs/data/medical-baseline-source.md` 출처 표기).
- 동물병원 ETL: `infra/etl/hospital_sync.py` — data.go.kr 농림축산식품부 동물병원 정보 API 페이지네이션 호출, upsert. 일일 cron(`0 4 * * *`) 또는 manual CLI 실행.
- Mock-first: `DATA_GO_KR_API_KEY` 미설정 시 `apps/api/seeds/hospitals_seoul_mock.json` (서울 50개 병원 fixture, 좌표 포함) 시딩.
- `Hospital` 모델 + Alembic `0006_hospital_postgis`: PostGIS POINT(geography, srid=4326) 컬럼, GiST 인덱스. `docker-compose.yml` 의 postgis/postgis:16-3.4 활용.
- 좌표 결측 시 카카오 로컬 API 지오코딩(`infra/etl/geocode.py`, `KAKAO_REST_API_KEY` 활용) 폴백, 실패 시 row 보류 + 로깅.
- `GET /v1/hospitals/nearby?lat=&lng=&radius_m=2000&limit=10` — `ST_DWithin(geog, ST_MakePoint(lng,lat)::geography, radius_m)` + `ST_Distance` 정렬 + 거리(m) 응답 필드.
- `GET /v1/hospitals/{id}` — 병원 상세(이름/주소/전화/영업시간/services/거리[옵셔널]).
- 모바일 홈 카드: `MedicalBudgetCard` (p50/p90 + "참고용 추정치, 의료 진단 아님" 디스클레이머, 적금 권장 placeholder는 "W4에 표시" 마이크로카피).
- 모바일 병원 화면: `apps/mobile/app/hospitals/index.tsx` (리스트 + 거리 정렬 상위 10) + `apps/mobile/app/hospitals/map.tsx` (KakaoMap WebView, W1/W2 spike 산출 컴포넌트 재사용, 상위 3개 마커) + 마커 탭 → `apps/mobile/app/hospitals/[id].tsx` 상세.
- shared-types codegen: diagnosis/medical_budget/hospital 스키마 추가, mobile typecheck 0 errors.
- mypy strict, ruff strict, coverage ≥ 80% 유지(W2 회복 수준).
- W4 카드 분해(`.omc/plans/w4-stage2-savings-donation-demo.md`) 초안 — Day 7 산출물(Stage 2 질병 LM, 적금 권장 카드 UI, 외부 가입 딥링크, mock-enroll, 후원, 90초 시연 영상, 5.25 제출).

### 1.2 Out of Scope (W4)

- Stage 2 질병 후보 LM(PetBERT/Transformer) fine-tune, `/infer/disease` 엔드포인트, `Diagnosis.top_diseases` 채우기 — W4.
- 적금 권장 카드 UI(`SavingsCard`), `recommended_monthly` 가시화, 가용 한도/마일리지 할증·할인 — W4.
- `SavingsProduct` 모델, `GET /v1/finance/savings`, 외부 가입 딥링크 트래킹 — W4.
- `POST /v1/finance/mock-enroll` PoC 가입 흐름 — W4.
- 후원 캠페인(`/v1/donations/*`), 농림축산식품부 보호소 데이터 ETL — W4.
- 90초 시연 영상 풀 시나리오, 시연 시드 시나리오(보리 시바·시니어 푸들) 영상화 — W4 Day 4(5.24).
- 사용자 프로필 quiet hours·가용 한도 설정 화면 — W4 또는 본선.
- Phase 2: gradient boosting(XGBoost/LightGBM) 의료비 모델, LoRA fine-tune cron, A/B 70/30 트래픽 — Out (본선 후).
- 산책 경로 기록(Polyline·background GPS), KakaoMap 옵션 A 네이티브 SDK 전환 — Out (Phase 2).

### 1.3 Constraints

- 로컬 AI 서버(RTX 5090)는 **별도 머신** + Cloudflare Tunnel 로 클라우드에서 접근. dev 환경에서는 `AI_SERVER_BASE_URL` 미설정 시 mock provider(deterministic anomaly 점수 반환) 자동 폴백. CI 도 동일.
- mTLS 인증서는 self-signed 로 우선 셋업, 본선 직전 정식 발급 검토. `AI_SERVER_SHARED_SECRET` HMAC 은 mTLS 와 별개로 항상 검증(이중 방어).
- Caretail 키 W2 가정 유지: 발급되었다고 가정하되 미발급 시 mock 14일 시드(W2 Day 4 결정적 anomaly 시그널 day 12~14 활동 30%↓·심박 10%↑) 로도 anomaly 모델 입력 충분.
- 4–5인 팀 분담 그대로(백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1). 5.17 일요일 작업 가능, 5.20 수요일 통합 안정화 데이로 신규 코드 동결 권장.
- Day 7(5.21)은 freeze + 통합 + W4 카드 분해 + 시연 storyboard 초안 전용. 신규 코드 금지.
- 의료/금융 디스클레이머 의무: 의료비 카드(spec 05 § 10), anomaly 알림(spec 02 § 7) 모두 "참고용 추정치, 의료 진단 아님" 또는 "통계·AI 추정치" 명시.
- PostGIS 가 docker-compose 에 이미 있다고 전제(W1 산출물). 없는 경우 Day 1 첫 30분에 image 교체 + `CREATE EXTENSION postgis;` 마이그레이션 선행.
- 베이스라인 시드 출처는 KB펫금융보고서·통계청·학회 자료로 한정, 출처 미상 셀은 `[추정]` 태그 + 출처 칼럼 빈 값.
- shared-types codegen 의 diagnosis 스키마는 `top_diseases: list[DiseaseProb]` 필드를 W3 시점에 빈 배열로 두되 *타입은 정의*해 W4 swap 부담 최소화.

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `alembic upgrade head` 실행 시 `diagnosis`, `medical_budget`, `hospital`(PostGIS POINT geography) 3개 테이블 + GiST 인덱스 생성, `CREATE EXTENSION IF NOT EXISTS postgis` 멱등 적용 | `psql -c "\dt"` + `psql -c "\d hospital"` + `\di hospital_geog_gix` 출력 검증 |
| AC2 | `apps/ai-server/` 가 `uv run uvicorn app.main:app --port 8001` 으로 기동되고 `GET /healthz` 200, `POST /infer/anomaly` 가 14일 feature vector 입력에 대해 `{score: float, contributions: [{feature, weight}]*3}` 반환 | `pytest apps/ai-server/tests/test_infer.py::test_anomaly_inference` |
| AC3 | 클라우드 API → AI 서버 호출이 mTLS + `X-AISERVER-SIG` HMAC 헤더를 부착하고, AI 서버는 위조 서명 거부(401) | `pytest apps/ai-server/tests/test_auth.py::test_hmac_required` + `pytest apps/api/tests/test_aiserver_client.py::test_hmac_signed` |
| AC4 | `AI_SERVER_BASE_URL` 미설정 또는 5초 타임아웃 시 `RuleAnomalyFallback` 자동 동작, `Diagnosis.source='fallback'` 표기 + `feature_contributions` 채워짐 | `pytest apps/api/tests/test_anomaly.py::test_fallback_on_timeout` (httpx mock으로 sleep 6초 시뮬레이션) |
| AC5 | `POST /v1/pets/{id}/health/analyze` 호출 시 직전 14일 daily_health 조회 → AI 서버 호출 → Diagnosis row 생성 → MedicalBudget recompute → 응답 `{diagnosis_id, anomaly_score, action, budget_id}` 반환, 가족 권한 검증 | `pytest apps/api/tests/test_analyze.py::test_analyze_full_flow_with_mock_aiserver` |
| AC6 | 의료비 예측식 단위 테스트: 동일 입력(breed=shiba, age=4, anomaly=0.0, chronic=[])에서 base p50=320,000원 ±5% (베이스라인 시드 기준), anomaly=0.5 입력 시 p50 약 1.30× 증가 | `pytest apps/api/tests/test_budget_predict.py::test_baseline_and_anomaly_multiplier` |
| AC7 | Bootstrap n=1000 결과의 p50/p90/CI 가 결정적(seed 고정) 재현 가능, CI_low ≤ p50 ≤ CI_high ≤ p90 | `pytest ::test_bootstrap_deterministic_and_monotone` |
| AC8 | 베이스라인 시드 `python -m app.seeds.medical_baseline` 실행 시 `breed_age_baseline` 테이블에 ≥ 30 row 적재, 출처 칼럼 ≥ 25 row 채워짐 | `pytest apps/api/tests/test_baseline_seed.py::test_baseline_min_30_rows_and_sources` |
| AC9 | `GET /v1/pets/{id}/budget` 가 최신 1건 반환, `POST /v1/pets/{id}/budget/recompute` 가 새 row 생성 후 200 반환, member 권한 통과 | `pytest apps/api/tests/test_budget.py::test_get_and_recompute_rbac` |
| AC10 | `python -m infra.etl.hospital_sync` 실행 시: ① `DATA_GO_KR_API_KEY` 설정 시 data.go.kr 페이지네이션 + upsert 동작, ② 미설정 시 `seeds/hospitals_seoul_mock.json` 50건 시딩 — 두 경로 모두 `hospital` 테이블 ≥ 50 row | `pytest infra/etl/tests/test_hospital_sync.py::test_real_and_mock_paths` (real 경로는 respx로 mock) |
| AC11 | `GET /v1/hospitals/nearby?lat=37.4979&lng=127.0276&radius_m=2000&limit=10` 가 ST_DWithin 으로 강남역 반경 2km 병원 ≥ 1건 반환, `distance_m` 오름차순 정렬 | `pytest apps/api/tests/test_hospitals.py::test_nearby_postgis_distance_sort` |
| AC12 | 좌표 결측 row 가 카카오 로컬 API 지오코딩 폴백을 거쳐 채워짐(respx mock 응답), 지오코딩 실패 시 row 는 `geog=NULL` 상태로 보류 + 로그 기록 | `pytest infra/etl/tests/test_geocode.py::test_geocode_fallback_and_skip` |
| AC13 | Mobile 홈에 `MedicalBudgetCard` 가 p50/p90(천원 단위 콤마 포맷) + 디스클레이머 + "월 권장 적금은 W4에 공개" 플레이스홀더 텍스트 동시 렌더 | `.omc/research/w3-demo.mp4` 30초 첨부, `docs/w3-demo.md` |
| AC14 | Mobile 병원 화면: 리스트 상위 10 + 지도 탭 KakaoMap WebView 에 상위 3 마커 + 사용자 위치 마커, 마커 탭 시 `app/hospitals/[id].tsx` 상세 화면으로 navigate | 시연 영상 동일 회차 |
| AC15 | `mypy app && mypy apps/ai-server/app` 0 errors, `ruff check .` 0 errors, `pytest --cov=app --cov-fail-under=80` 통과, `pnpm -C apps/mobile typecheck` 0 errors | CI 로그 (`.github/workflows/api.yml`, `.github/workflows/aiserver.yml`) green |

> Done 임계: 15개 중 ≥ 12개 통과. 미통과는 W4 첫날 보강 카드.

---

## 3. Implementation Steps (Day 단위)

### 3.1 Day 1 (5.15 금) — AI 서버 스캐폴딩 + Diagnosis/MedicalBudget 모델 + PostGIS 셋업

> W2 freeze 해제. 로컬 AI 서버 첫 도입이므로 인프라·모델·DB 동시 진행.

#### 트랙 A · 로컬 AI 서버 스캐폴딩 (AI/infra)
- [ ] `apps/ai-server/` 생성: `pyproject.toml`(uv 기반, fastapi/uvicorn/scikit-learn/numpy/pydantic 의존), `app/main.py`, `app/routers/infer.py`, `app/services/anomaly.py`, `app/auth/hmac.py`.
- [ ] `app/services/anomaly.py` — `IsolationForest(n_estimators=100, contamination=0.1, random_state=42)` 모델 + `rolling z-score`(window=7) 앙상블. 입력: `np.ndarray shape=(14, 4)` (활동/심박/수면/체중변화율), 출력: `(score: float, contributions: list[tuple[str, float]])`.
- [ ] `app/auth/hmac.py` — `verify_signature(body: bytes, signature: str, secret: str) -> bool` (timing-safe compare).
- [ ] `app/routers/infer.py` — `POST /infer/anomaly` body `{pet_id, features: [[...],...]*14}`. HMAC 검증 dependency.
- [ ] `apps/ai-server/Dockerfile` + `docker-compose.yml` 에 `aiserver` 서비스(외부 노출 포트 8001, dev only).
- [ ] mTLS 인증서: `infra/certs/aiserver-{ca,cert,key}.pem` self-signed 생성 스크립트(`infra/scripts/gen_aiserver_certs.sh`).
- [ ] `apps/ai-server/tests/test_infer.py` — AC2.
- [ ] `apps/ai-server/tests/test_auth.py` — AC3 (server 측).

#### 트랙 B · DB 모델 + Alembic 마이그레이션 (backend lead)
- [ ] `apps/api/app/models/diagnosis.py`: `Diagnosis(id, pet_id FK, ts, anomaly_score, feature_contributions jsonb, top_diseases jsonb default '[]', action enum('immediate','schedule','observe'), source enum('aiserver','fallback','mock'), medical_budget_id FK→medical_budget nullable)`.
- [ ] `apps/api/app/models/medical_budget.py`: `MedicalBudget(id, pet_id FK, computed_at, horizon_months default 12, p50 int, p90 int, ci_low int, ci_high int, drivers jsonb, recommended_monthly int, diagnosis_id FK→diagnosis nullable, baseline_key str)`.
- [ ] `apps/api/app/models/breed_age_baseline.py`: `BreedAgeBaseline(id, breed_size enum, life_stage enum('puppy','adult','senior'), p50 int, p90 int, ci_low int, ci_high int, source str, source_url str|null, note str|null)` — composite unique (breed_size, life_stage, baseline_key).
- [ ] `apps/api/app/models/hospital.py`: `Hospital(id, name, address, phone|null, hours jsonb|null, services jsonb|null, public_data_id str unique|null, lat float|null, lng float|null, geog Geography(Point, 4326)|null, region str, last_synced_at)` — `geoalchemy2` 의존 추가.
- [ ] `alembic revision --autogenerate -m "0004_diagnosis_anomaly"` → `0005_medical_budget` → `0006_hospital_postgis` (3개 분할). `0006` 에 `op.execute("CREATE EXTENSION IF NOT EXISTS postgis")` + `CREATE INDEX hospital_geog_gix ON hospital USING gist(geog)`.
- [ ] AC1 검증: `alembic upgrade head && psql -c "\dt"`.

#### 트랙 C · 클라우드 API ↔ AI 서버 클라이언트 (backend dev)
- [ ] `apps/api/app/integrations/aiserver/__init__.py` — `AnomalyProvider` Protocol (`async def infer(features: list[list[float]]) -> AnomalyResult`).
- [ ] `apps/api/app/integrations/aiserver/client.py` — `RealAnomalyProvider`: httpx AsyncClient + mTLS(`cert=(client_cert, client_key), verify=ca_cert`) + HMAC 서명 헤더 부착 + 5초 timeout + 429/5xx 재시도(max 1회).
- [ ] `apps/api/app/integrations/aiserver/fallback.py` — `RuleAnomalyFallback`: 활동 분 30%↓ + 심박 10%↑ + 수면 deep ratio 20%↓ 룰 → score 가중합 + sigmoid.
- [ ] `apps/api/app/integrations/aiserver/mock.py` — 결정적 mock(W2 mock 14일 시드 패턴에 맞춰 day 12~14 anomaly score=0.78 반환).
- [ ] `apps/api/app/integrations/aiserver/factory.py` — `AI_SERVER_BASE_URL` + cert 파일 존재 시 real, 없으면 mock. 5초 타임아웃 시 자동으로 fallback로 강등(provider 데코레이터).
- [ ] `apps/api/tests/test_aiserver_client.py` — AC3 client 측.

#### 트랙 D · 베이스라인 시드 데이터 수집·검증 (리드/PM)
- [ ] `docs/data/medical-baseline-source.md` 신규 — KB펫금융보고서/통계청/학회 자료 출처 1차 정리.
- [ ] `apps/api/seeds/medical_baseline.py` 초안: `BreedAgeBaseline` 30+ row 시드 데이터 dict 작성.
  - breed_size: xs(<5kg), sm(5~10kg), md(10~25kg), lg(>25kg)
  - life_stage: puppy(<1y), adult(1~7y), senior(>7y)
  - 셀당 baseline_key='annual' 기본 + (선택) 'preventive', 'emergency' 2개 추가 → 4×3×3 = **36 셀**.

**Day 1 종료 조건**: AC1 통과. `apps/ai-server` 가 로컬에서 기동되고 `curl localhost:8001/healthz` 200. AC8용 시드 데이터 ≥ 30 dict 작성 완료(아직 적재 X).

---

### 3.2 Day 2 (5.16 토) — AI 서버 추론 완성 + 베이스라인 시드 적재 + 의료비 예측식 1차

#### 트랙 A · AI 서버 IsolationForest + z-score 앙상블 (AI/infra)
- [ ] `apps/ai-server/app/services/anomaly.py` 본 구현:
  - 학습 데이터 부족(첫 도입) → IsolationForest 는 *fit-on-the-fly* 전략 사용: 입력 14일 + 사전 시드(`apps/ai-server/seeds/anomaly_train.npy` 200 sample) 합쳐 fit 후 마지막 row 점수 추출.
  - z-score: 각 feature 별 14일 rolling mean/std 대비 마지막 day z, |z| > 2 시 가중.
  - 앙상블: `score = sigmoid(0.6 * iforest_score_norm + 0.4 * max_z_norm)`.
  - 기여 feature top-3: |z| 절댓값 + IF feature_importances_ 보간 → 정렬.
- [ ] `apps/ai-server/seeds/anomaly_train.npy` 생성 스크립트(`apps/ai-server/seeds/build_train.py`) — Caretail mock 14일 시드 14개 펫 분 + 합성 anomaly 패턴.
- [ ] AC2 마무리.

#### 트랙 B · 의료비 예측식 + Bootstrap CI (backend lead)
- [ ] `apps/api/app/services/budget_predict.py`:
  ```python
  ALPHA = 0.6        # anomaly weight
  BETA = 0.0         # disease weight (W3 disabled, W4 enable)
  GAMMA_PER_CHRONIC = 0.2
  GAMMA_CAP = 0.6
  BOOTSTRAP_N = 1000
  RNG_SEED = 20260515
  ```
  - `predict(pet, baseline, anomaly_score, top_diseases=[]) -> BudgetResult`
  - `bootstrap(base_p50, base_p90, multiplier, n=1000) -> (p50, p90, ci_low, ci_high)` — 정규 노이즈 σ=0.15·base 기반 샘플 → 분위수.
  - drivers: `["chronic:신장"]`, `["anomaly:0.62"]` 형식.
- [ ] `apps/api/tests/test_budget_predict.py` — AC6, AC7.

#### 트랙 C · 베이스라인 시드 적재 + Diagnosis/Budget 서비스 (backend dev)
- [ ] `apps/api/seeds/medical_baseline.py` 완성: 36 셀 dict → DB upsert. CLI: `python -m app.seeds.medical_baseline`.
- [ ] `apps/api/tests/test_baseline_seed.py` — AC8.
- [ ] `apps/api/app/services/diagnosis.py` — `analyze_pet(pet_id) -> DiagnosisResult`: daily_health 14일 fetch → feature 정규화 → AnomalyProvider.infer → Diagnosis 저장 → action 결정.
- [ ] `apps/api/app/services/budget.py` — `recompute(pet_id, diagnosis=None) -> MedicalBudget`: pet meta 조회 → baseline 룩업(breed_size·life_stage 매핑 헬퍼) → predict → MedicalBudget upsert.

#### 트랙 D · Hospital ETL 1차 (mock 경로 우선) (AI/infra)
- [ ] `apps/api/seeds/hospitals_seoul_mock.json` — 서울 25개 구 × 평균 2개 = **50개** 병원 fixture (이름·주소·전화·lat·lng·hours mock).
  - 출처: 공공데이터 샘플 + 카카오맵 검색 결과 [추정 — Day 5에 lead 가 1차 검수].
- [ ] `infra/etl/__init__.py`, `infra/etl/hospital_sync.py` 신규: `sync(api_key: str | None) -> int` — 키 있으면 data.go.kr API, 없으면 fixture upsert.
- [ ] `infra/etl/tests/test_hospital_sync.py` — AC10 mock 경로 우선.

**Day 2 종료 조건**: AC2, AC6, AC7, AC8 통과. AC10의 mock 경로 통과.

---

### 3.3 Day 3 (5.17 일) — 클라우드 API 통합 + analyze/budget/hospital 엔드포인트

#### 트랙 A · `/v1/pets/{id}/health/analyze` + `/v1/pets/{id}/budget` (backend lead)
- [ ] `apps/api/app/api/v1/health.py` 에 `POST /{id}/health/analyze` 추가:
  - 가족 권한(`require_family(role='member')`).
  - `services.diagnosis.analyze_pet` → `services.budget.recompute` 순차 호출.
  - 응답 `{diagnosis_id, anomaly_score, action, budget_id, source}`.
- [ ] `apps/api/app/api/v1/budget.py` 신규:
  - `GET /v1/pets/{id}/budget` — 최신 1건, 없으면 자동 recompute 1회.
  - `POST /v1/pets/{id}/budget/recompute` — 강제 재계산.
- [ ] `apps/api/tests/test_analyze.py` — AC5 (mock AI provider 사용).
- [ ] `apps/api/tests/test_budget.py` — AC9.
- [ ] `apps/api/tests/test_anomaly.py` — AC4 (timeout fallback).

#### 트랙 B · 병원 nearby + 상세 + 권한 (backend dev)
- [ ] `apps/api/app/api/v1/hospitals.py` 신규:
  - `GET /v1/hospitals/nearby?lat=&lng=&radius_m=2000&limit=10` — `ST_DWithin(geog, ST_MakePoint(lng,lat)::geography, radius_m)` 쿼리 + `ST_Distance` 정렬 + `distance_m` 응답 필드. 인증 필요(가족 컨텍스트는 불필요, 사용자 인증만).
  - `GET /v1/hospitals/{id}` — 상세.
  - 좌표 검증: |lat|<=90, |lng|<=180, radius_m ∈ [100, 20000], limit ∈ [1, 50].
- [ ] `apps/api/tests/test_hospitals.py` — AC11 (testcontainers postgis 또는 dev DB 활용).

#### 트랙 C · Mobile 의료비 카드 + 병원 API 훅 (mobile dev)
- [ ] `apps/mobile/src/api/budget.ts` — `useBudget(petId)`, `useRecomputeBudget`.
- [ ] `apps/mobile/src/api/hospitals.ts` — `useNearbyHospitals(lat, lng, radiusM)`, `useHospital(id)`.
- [ ] `apps/mobile/src/components/MedicalBudgetCard.tsx` — p50/p90 표시 + 디스클레이머 + W4 placeholder.
- [ ] `apps/mobile/app/(tabs)/index.tsx` — 홈 화면에 카드 추가(W2 sparkline·도넛 하단).
- [ ] AC13 사전 점검(데이터 mock 으로 1차 렌더).

#### 트랙 D · 통합 미팅 (5.17 W3 중간 점검, external-apis.md § 7) (PM)
- [ ] data.go.kr 키 발급 상태, 카카오 JS 키 도메인 등록 상태, Caretail OAuth 응답 상태 점검 → fallback 결정 확정.
- [ ] mTLS 인증서 self-signed 사용 결정 vs 정식 발급 일정 결정.

**Day 3 종료 조건**: AC4, AC5, AC9, AC11 통과. 모바일 홈에 MedicalBudgetCard 가 mock 데이터로 표시.

---

### 3.4 Day 4 (5.18 월) — 동물병원 ETL real 경로 + 지오코딩 + KakaoMap WebView 마커

#### 트랙 A · data.go.kr Real 경로 + 지오코딩 폴백 (AI/infra)
- [ ] `infra/etl/hospital_sync.py` real 경로 본 구현:
  - `httpx.AsyncClient` + `params={"serviceKey": ..., "pageNo": n, "numOfRows": 100, "type": "json"}`.
  - 페이지네이션 (총 row 추정 → 1000건/페이지 × N pages, 안전상한 50 pages).
  - upsert by `public_data_id`.
  - 좌표 결측 시 `infra.etl.geocode.geocode_address(addr)` 호출.
- [ ] `infra/etl/geocode.py` — 카카오 로컬 API `GET https://dapi.kakao.com/v2/local/search/address.json?query={addr}` (`Authorization: KakaoAK {KAKAO_REST_API_KEY}`), 결과 첫 row x/y → lng/lat 매핑.
- [ ] 실패 시 row 보류 + 구조적 로그(`logger.warning(extra={"hospital_id": ..., "addr": ..., "reason": ...})`).
- [ ] `infra/etl/tests/test_geocode.py` — AC12 (respx로 카카오 API mock).
- [ ] `infra/etl/tests/test_hospital_sync.py` real 경로 추가 — AC10 마무리.
- [ ] cron 등록: `infra/cron/hospital_sync.crontab` 또는 docker-compose 에 cron 컨테이너(or 일단 manual CLI 만 W3 인정).

#### 트랙 B · Mobile 병원 리스트 + 지도 화면 (mobile dev)
- [ ] `apps/mobile/app/hospitals/index.tsx` — 사용자 위치(`expo-location`) 획득 → `useNearbyHospitals` → 리스트 상위 10. 거리(m) 표기, "지도로 보기" 버튼.
- [ ] `apps/mobile/app/hospitals/map.tsx` — W1 spike 의 `KakaoMapWebView` 컴포넌트 재사용. 상위 3개 마커 + 사용자 위치 마커. `onHospitalSelect` → `router.push('/hospitals/' + id)`.
- [ ] `apps/mobile/app/hospitals/[id].tsx` — 상세 화면(이름/주소/전화/영업시간/services/거리/지도 미니뷰).
- [ ] 상세 화면에서 "이 병원에 진료 일정 추가" 버튼 → W2 의 `app/calendar/new.tsx` 로 prefill 진입.

#### 트랙 C · 모바일 홈 의료비 카드 폴리싱 + 디스클레이머 (mobile dev 또는 backend dev 보조)
- [ ] `MedicalBudgetCard` 디자인 마무리: p50 / p90(천원 단위), drivers 칩(상위 2개), "참고용 추정치, 의료 진단 아님" 푸터, "이번 달 권장 적금은 W4에 공개" 마이크로카피.
- [ ] 적금 권장 슬롯은 placeholder 컴포넌트로 유지(W4 swap 지점 명확화).

#### 트랙 D · shared-types codegen 확대 (backend dev)
- [ ] `packages/shared-types/openapi.ts` 재생성 — diagnosis, medical_budget, breed_age_baseline, hospital(좌표·distance_m 포함) 스키마 추가.
- [ ] `apps/mobile/src/api/types.ts` import 정리, `pnpm typecheck` 0 errors (AC15 사전 확인).

**Day 4 종료 조건**: AC10 real 경로 + AC12 통과. 모바일에서 병원 리스트·지도·상세 navigate 동작(mock or real ETL 데이터).

---

### 3.5 Day 5 (5.19 화) — E2E 시연 시드 시나리오 + 시연 영상 30초

#### 트랙 A · E2E 시연 시드 시나리오 적재 (backend lead + AI/infra)
- [ ] `apps/api/seeds/demo_w3.py` 신규:
  - 시나리오 1: 보리(시바·md·adult·기저없음) 14일 mock 헬스 데이터 → analyze → anomaly 0.62, p50 약 32만, p90 약 50만, action='schedule'.
  - 시나리오 2: 시니어 푸들(sm·senior·신장질환) 14일 mock + day 13~14 활동 35%↓ → anomaly 0.78, p50 약 80만, p90 약 130만, action='immediate'.
  - 두 시나리오 모두 spec 05 § 9 의 검증 시드와 *수치 정합* (±10% 허용).
- [ ] `apps/api/tests/test_demo_scenarios.py` — 두 시나리오 회귀 테스트 추가.

#### 트랙 B · 시연 영상 30초 + AC13/AC14 마무리 (mobile dev + lead)
- [ ] 시연 흐름: 로그인(mock) → 펫 선택(보리) → 홈(sparkline + MedicalBudgetCard p50/p90) → 병원 탭 → 리스트 → 지도 마커 3개 → 마커 탭 → 상세.
- [ ] `.omc/research/w3-demo.mp4` 1차 촬영(30초), `docs/w3-demo.md` 시나리오 메모.
- [ ] 디스클레이머 3종 모두 화면에 노출 확인(의료/금융/적금 W4 placeholder).

#### 트랙 C · 통합 안정화 + mypy/ruff/coverage 점검 (backend dev)
- [ ] `mypy app && mypy apps/ai-server/app` 0 errors 확인 (W2 회복 수준 유지).
- [ ] `ruff check . --fix` 후 잔여 정리.
- [ ] `pytest --cov=app --cov-fail-under=80` 통과. AI 서버 측은 별도 커버리지 별도 측정(목표 ≥ 70%).
- [ ] AI 서버 mTLS·HMAC E2E 1회 수동 점검 (Day 7 freeze 전 마지막 안전망).

#### 트랙 D · Caretail/data.go.kr 키 상태 갱신 (PM)
- [ ] `.omc/research/api-applications/` 키 상태 스냅샷 갱신, W4 위험 입력.

**Day 5 종료 조건**: AC13, AC14 통과 + 시연 시드 시나리오 2건 회귀 통과.

---

### 3.6 Day 6 (5.20 수) — 통합 안정화 + W4 카드 분해 초안

> **신규 기능 코드 동결 권장**. 통합 안정화·문서·차주 카드.

- [ ] `mypy && ruff && pytest --cov-fail-under=80` 최종 회귀 (AC15 사전).
- [ ] `pnpm -C apps/mobile typecheck` 0 errors (AC15 사전).
- [ ] `apps/ai-server` 회귀: `pytest apps/ai-server/tests/` + 수동 inference 1회.
- [ ] OpenAPI export → `docs/api/openapi-w3.json` (diagnosis/budget/hospital 포함).
- [ ] `docs/w3-retrospective.md` 초안.
- [ ] `.omc/plans/w4-stage2-savings-donation-demo.md` 초안 — Stage 2 LM(`/infer/disease`), MedicalBudget β·disease term 활성화, SavingsCard UI, `GET /v1/finance/savings`, `POST /v1/finance/mock-enroll`, 후원 캠페인, 90초 시연 영상(5.24 촬영), 5.25 제출 흐름까지 5일 분배(5.22 ~ 5.25, 단축 주차).
- [ ] `docs/spikes/aiserver-mtls.md` 신규 — mTLS 셋업 절차·HMAC 헤더 사양·정식 인증서 발급 옵션.

**Day 6 종료 조건**: 신규 코드 0 줄, 모든 테스트 green, W4 카드 초안 존재.

---

### 3.7 Day 7 (5.21 목) — Freeze · 통합 · W4 카드 확정 · 시연 storyboard

- [ ] AC1~AC15 점검표 갱신, 통과 ≥ 12 확인. 미통과는 W4 첫날 보강 카드로 이월.
- [ ] `docs/w3-retrospective.md` 마무리 — 잘 된 것/막힌 것/W4 이월.
- [ ] `.omc/plans/w4-stage2-savings-donation-demo.md` 확정(리뷰 1회).
- [ ] 시연 storyboard 초안 작성(`docs/demo-storyboard-w4.md`): 90초 시나리오 컷별 시점·자막·BGM·디스클레이머 포지션.
- [ ] CI green 확인(`api.yml`, `aiserver.yml`).
- [ ] `.omc/research/api-applications/` 최종 스냅샷 + W4 진입 위험 1-pager.

---

## 4. 위험 · 대응

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | 로컬 AI 서버(RTX 5090) Cloudflare Tunnel 두절 또는 5090 머신 다운 | 中 | 高 | factory 가 5초 타임아웃 시 `RuleAnomalyFallback` 자동 강등(AC4), `Diagnosis.source='fallback'` 표기. 시연 시 mock provider 강제 활성 옵션(`AI_SERVER_FORCE_MOCK=1`). 본선 직전 lightweight ONNX CPU 백업 모델 검토(spec 02 § 7). |
| R2 | data.go.kr 동물병원 API 키 발급 지연 또는 응답 스키마 변경 | 中 | 中 | `seeds/hospitals_seoul_mock.json` 50건 fixture 우선 동작(AC10 mock 경로). real 경로는 키 발급 후 Day 4 swap, 실패 시 W4 첫날 보강. |
| R3 | 카카오 로컬 API 지오코딩 일일 quota(REST 키 기준 30만 호출/일) 초과 | 低 | 中 | ETL 1회 실행당 좌표 결측 row 만 호출 + 결과 캐싱(`hospital.geog` 영구 저장 후 재시도 X). batch 1000 미만으로 분할. |
| R4 | mTLS 인증서 self-signed 로 인한 클라이언트 검증 실패(httpx `verify` 옵션) | 中 | 中 | `verify=ca_cert_path` 명시 + `apps/api/app/integrations/aiserver/client.py` 단위 테스트로 cert 핸드셰이크 회귀. dev 환경은 `VERIFY_AISERVER_TLS=0` 환경변수로 우회 옵션(production 절대 금지 주석). |
| R5 | 베이스라인 시드 출처 검증이 Day 5 까지 미완료 | 中 | 中 | Day 1 PM 트랙으로 `medical-baseline-source.md` 1차 수집 의무, 부족 셀은 `[추정]` 태그 + 출처 빈 칼럼 허용. AC8 은 ≥ 25 row 출처 채워짐을 임계로 완화. |
| R6 | PostGIS extension 이 docker-compose 의 postgres 이미지에 미포함 | 低 | 高 | `docker-compose.yml` 의 image 를 `postgis/postgis:16-3.4` 로 명시(W1 산출 가정), 누락 시 Day 1 첫 30분에 image 교체 + `CREATE EXTENSION` 마이그레이션 선행. CI 에서도 동일 image 사용. |
| R7 | IsolationForest fit-on-the-fly 가 14 sample 만으로는 anomaly 시그널 약함 | 中 | 中 | 사전 시드 학습 데이터 200 sample (`apps/ai-server/seeds/anomaly_train.npy`) 와 합쳐 fit, z-score 앙상블 가중(0.4) 로 보강. AC2 는 mock 14일 day 12~14 패턴에서 score ≥ 0.6 임계로 완화. |
| R8 | shared-types codegen 의 diagnosis.top_diseases 빈 배열 타입이 W4 swap 시 호환 깨짐 | 低 | 中 | W3 시점부터 `top_diseases: list[DiseaseProb]` 타입을 정의하고 빈 배열로 두기, W4 는 *값만* 채움. `DiseaseProb {label, prob, confidence_band}` 인터페이스 W3 codegen 에 포함. |
| R9 | 5.17 일요일 인력 부재 또는 5.20 수요일 통합 안정화가 하루로 부족 | 中 | 中 | Day 3(일)은 트랙 A/B 위주(분담 가능), Day 6(수)은 신규 코드 동결로 비동기 작업 가능. 부족 시 Day 7 freeze 일부 시간 통합으로 전환 + W4 카드 보강. |
| R10 | Bootstrap CI 결과가 매 호출마다 달라져 시연 영상 재현 불가 | 低 | 中 | `RNG_SEED=20260515` 고정(numpy `np.random.default_rng(seed)`). 시연 시드 시나리오는 별도 회귀 테스트(AC7)로 보호. |

---

## 5. Verification Steps

### 5.1 자동
```bash
# 0) PostGIS 컨테이너 + 의존
cd /home/hidi/dev/health_pet
docker compose up -d postgres redis worker
docker compose up -d aiserver       # apps/ai-server 컨테이너

# 1) 클라우드 API
cd apps/api
uv pip install -e ".[dev]"
alembic upgrade head                # AC1
python -m app.seeds.medical_baseline
python -m infra.etl.hospital_sync   # mock 또는 real 자동 분기
pytest -v --cov=app --cov-fail-under=80
ruff check .
mypy app                            # 0 errors

# 2) AI 서버
cd ../ai-server
uv pip install -e ".[dev]"
pytest -v
mypy app                            # 0 errors

# 3) shared-types + mobile
cd ../../packages/shared-types
pnpm codegen
cd ../../apps/mobile
pnpm typecheck                      # AC15
```

### 5.2 수동 (AC13, AC14)
1. `pnpm -C apps/mobile start` → 로그인(mock) → 가족 → 펫(보리) 선택.
2. 홈 화면: sparkline + MedicalBudgetCard(p50 32만, p90 50만, 디스클레이머) 동시 렌더 확인.
3. 병원 탭 → GPS 권한 허용 → 리스트 상위 10 거리(m) 정렬 확인.
4. "지도로 보기" → KakaoMap WebView 마커 3개 + 사용자 위치.
5. 마커 탭 → 병원 상세(이름/주소/전화/영업시간) → "진료 일정 추가" 진입까지.
6. `POST /v1/pets/{id}/health/analyze` curl 1회 → Diagnosis + MedicalBudget 새 row 생성 확인 (`psql -c "SELECT * FROM diagnosis ORDER BY ts DESC LIMIT 1"`).
7. 30초 시연 영상 → `.omc/research/w3-demo.mp4`.

### 5.3 종료 점검 (Day 7 PM)
- AC 통과 < 12 → W4 첫날 보강 카드 삽입.
- AI 서버 mTLS·HMAC E2E 수동 점검 1회 통과 확인.
- `.omc/plans/w4-stage2-savings-donation-demo.md` 존재 + 5.22~5.25 일정 분배 명확.

---

## 6. Team Allocation (4–5인)

| 트랙 | 인력 | 주요 산출 |
|---|---|---|
| Backend Lead | 1 | Diagnosis/MedicalBudget 모델·Alembic·analyze/budget API·예측식·bootstrap·시연 시드 시나리오 |
| Backend Dev | 1 | hospitals API·shared-types codegen·베이스라인 시드 적재·budget 서비스·통합 테스트 |
| Mobile Dev | 1 | MedicalBudgetCard·병원 리스트/지도/상세·KakaoMap WebView 재사용·시연 영상 촬영 |
| AI/Infra | 1 | apps/ai-server FastAPI·IsolationForest+z-score·HMAC·mTLS 인증서·hospital ETL·지오코딩 |
| Lead/PM (5명일 때) | 1 | 베이스라인 출처 검증·키 상태 추적·디스클레이머/문서 검수·W4 카드 분해·시연 storyboard |

> 4명 운영 시 Lead/PM 역할을 Backend Lead 가 겸직, 시연 영상은 Mobile Dev 가 촬영. 베이스라인 출처 검증은 Day 1~2 분할.

---

## 7. File Map

```
apps/ai-server/                                              [new package]
  pyproject.toml
  app/main.py
  app/routers/infer.py
  app/services/anomaly.py
  app/auth/hmac.py
  seeds/anomaly_train.npy                                    [new, generated]
  seeds/build_train.py                                       [new]
  tests/test_infer.py                                        [new, AC2]
  tests/test_auth.py                                         [new, AC3]
  Dockerfile                                                 [new]

apps/api/
  alembic/versions/0004_diagnosis_anomaly.py                 [new]
  alembic/versions/0005_medical_budget.py                    [new]
  alembic/versions/0006_hospital_postgis.py                  [new, CREATE EXTENSION + GiST]
  app/models/diagnosis.py                                    [new]
  app/models/medical_budget.py                               [new]
  app/models/breed_age_baseline.py                           [new]
  app/models/hospital.py                                     [new, geoalchemy2 Geography]
  app/api/v1/health.py                                       [edit: POST /analyze]
  app/api/v1/budget.py                                       [new]
  app/api/v1/hospitals.py                                    [new]
  app/services/diagnosis.py                                  [new]
  app/services/budget.py                                     [new]
  app/services/budget_predict.py                             [new, formula + bootstrap]
  app/services/anomaly_fallback.py                           [new, rule-based]
  app/integrations/aiserver/{__init__,client,fallback,
                              mock,factory}.py               [new]
  seeds/medical_baseline.py                                  [new, 36 cells]
  seeds/hospitals_seoul_mock.json                            [new, 50 hospitals]
  seeds/demo_w3.py                                           [new, 시연 시드 시나리오]
  tests/test_aiserver_client.py                              [new, AC3]
  tests/test_anomaly.py                                      [new, AC4]
  tests/test_analyze.py                                      [new, AC5]
  tests/test_budget_predict.py                               [new, AC6, AC7]
  tests/test_baseline_seed.py                                [new, AC8]
  tests/test_budget.py                                       [new, AC9]
  tests/test_hospitals.py                                    [new, AC11]
  tests/test_demo_scenarios.py                               [new]

infra/etl/
  __init__.py                                                [new]
  hospital_sync.py                                           [new, AC10]
  geocode.py                                                 [new, AC12]
  tests/test_hospital_sync.py                                [new]
  tests/test_geocode.py                                      [new]

infra/cron/hospital_sync.crontab                             [new, optional]
infra/certs/aiserver-{ca,cert,key}.pem                       [new, gitignored]
infra/scripts/gen_aiserver_certs.sh                          [new]

apps/mobile/
  src/api/budget.ts                                          [new]
  src/api/hospitals.ts                                       [new]
  src/components/MedicalBudgetCard.tsx                       [new]
  app/(tabs)/index.tsx                                       [edit: card 추가]
  app/hospitals/index.tsx                                    [new]
  app/hospitals/map.tsx                                      [new, KakaoMap WebView 재사용]
  app/hospitals/[id].tsx                                     [new]

packages/shared-types/                                        [edit: diagnosis/budget/hospital 추가]

docs/
  data/medical-baseline-source.md                            [new]
  spikes/aiserver-mtls.md                                    [new]
  w3-demo.md                                                 [new]
  w3-retrospective.md                                        [new]
  api/openapi-w3.json                                        [generated]
  demo-storyboard-w4.md                                      [new, Day 7 산출]

.omc/plans/w4-stage2-savings-donation-demo.md                [new, Day 6~7 산출]
.omc/research/w3-demo.mp4                                    [new]

docker-compose.yml                                           [edit: aiserver 서비스 + postgis image 확정]
.github/workflows/aiserver.yml                               [new]
```

---

## 8. Done Definition

- [ ] AC1~AC15 중 ≥ 12개 통과(목표 13~14).
- [ ] mypy 0 errors (api + ai-server), ruff 0 errors, coverage ≥ 80% (api), ≥ 70% (ai-server) (AC15).
- [ ] shared-types codegen 적용, mobile typecheck 0 errors (AC15).
- [ ] 30초 W3 시연 영상 1회 (`.omc/research/w3-demo.mp4`).
- [ ] `.omc/plans/w4-stage2-savings-donation-demo.md` 초안 존재 + 5.22~5.25 일정 분배.
- [ ] `docs/w3-retrospective.md` 작성.
- [ ] `docs/demo-storyboard-w4.md` 초안 존재.
- [ ] CI green (`.github/workflows/api.yml`, `.github/workflows/aiserver.yml`).
- [ ] mTLS·HMAC E2E 수동 점검 1회 통과.

---

## 9. Open Questions

1. 로컬 AI 서버 정식 mTLS 인증서 발급 — W3 self-signed 로 시연하고 본선(6.5 이후) 정식 발급 vs W4 중 정식 발급 결정 필요. 현재 가정: self-signed + HMAC 이중 검증으로 5.25 제출 충분.
2. 베이스라인 시드 36 셀 중 출처 미상 셀 비율 한도 — 현재 AC8 임계는 ≥ 25/30 채움. 출처 미상이 5 셀 초과 시 시연 슬라이드에 "추정치 포함" 표기 필요. PM 1차 수집 결과에 따라 5.18 까지 결정.
3. 의료비 예측식 계수 α=0.6, γ=0.2 — 시드 데이터·문헌 기반 grid search 는 W3 일정 부족, 현재 hand-tuned 상수. W4 또는 본선에서 sklearn `GridSearchCV` 또는 베이지안 옵티마이저로 fit 검토.
4. PostGIS 의존(`geoalchemy2`) 이 mypy strict 와 충돌 가능 — `geoalchemy2.types.Geography` 타입 stub 존재 여부 확인 필요. 없으면 `[mypy.geoalchemy2]` 모듈 한정 `ignore_missing_imports = True` 완화.
5. data.go.kr 동물병원 API 의 정확한 데이터셋 이름·버전 — "농림축산식품부 동물병원 정보" vs "LOCALDATA 수의업" 중 첫 호출 성공한 쪽으로 확정. 응답 스키마 차이는 `infra/etl/hospital_sync.py` 의 어댑터 함수로 흡수.
6. 카카오 JS API 도메인 등록 상태 — W1 spike 결정대로 `localhost` + `autoload=false` 패턴 유지 vs W3 시점에 `petfinect.app` 등 정식 도메인 등록 결정. 시연 안정성 우선 시 정식 도메인 등록 권장.
7. AI 서버 시드 학습 데이터 200 sample (`anomaly_train.npy`) 출처 — Caretail mock 14일 시드 펫 14마리 분 + 합성 anomaly 패턴이 통계적으로 충분한지 Day 2 검증 필요. 부족 시 합성 데이터 LLM 증강(spec 02 § 3.5).
8. `MedicalBudget.recommended_monthly` 필드는 W3 모델에 포함되지만 W3 UI 에는 *비노출*. 값 자체는 `ceil(p90/12/1000)*1000` 으로 채워두고 W4 SavingsCard 가 읽음. 의도적 결정 — 변경 시 W4 카드 영향.

---

## 10. Changelog

- 2026-05-04 — 초안 작성. W2 산출물(Pet/Family/Caretail polling/daily_health/푸시) 가정. 로컬 AI 서버(RTX 5090) 도입 첫 주차, mTLS+HMAC 이중 검증, 5초 타임아웃 룰 기반 fallback. 의료비 예측식 W3 disease term=0 단락, anomaly+chronic 만으로 p50/p90+CI 산출. 동물병원 PostGIS 근접 검색 + 카카오맵 WebView 마커(W1 spike 컴포넌트 재사용). Stage 2 LM·적금 권장 카드·후원·시연 영상은 W4 이월(5.22~5.25 단축 주차).
