# W4 Plan · Stage 2 질병 LM + 적금/후원 통합 + 시연 영상 (FINAL WEEK)

> 기간: 2026-05-22(금) ~ 2026-05-25(월), **4일** · 4–5인 팀 · **5.25 17:00 KST 서류심사 마감**
> 상위 plan: `~/.claude/plans/ai-compressed-codd.md` § 10 W4 / `docs/specs/02-health-analysis.md` § 3 (Stage 2 LM, /infer/disease, mTLS) / `docs/specs/05-medical-budget-savings.md` § 3~6 (savings·donation·디스클레이머) / `docs/proposal-outline.md` § 3 (90초 시연 컷 시트)
> 모드: W3까지 mock-first 유지된 적금·후원·Stage 2 분기를 **데모 가능 상태**로 좁히고, 마지막 날(5.25)은 **하드 프리즈 + 영상 + 제출 패키지** 전용. 신규 코드 금지. W4 전체 톤: "구현 절반 + QA·영상 절반". W2/W3 보다 strict (Done 임계 ≥ 9/10).

---

## 1. Requirements Summary

W4 종료 시점(5.25 17:00 KST)에 **Stage 2 질병 LM(/infer/disease) 추론 → MedicalBudget β 항 갱신 → 적금 권장 카드 → 외부 가입/mock 가입/나중에 3-CTA → 후원 캠페인 카드** 까지 한 흐름으로 시연 가능해야 한다. E2E 시연은 `apps/api/seeds/demo_scenarios.py --reset` 한 줄 실행으로 결정적으로 재현되며(시나리오 A·B 2종), 90초 시연 영상(`.omc/research/w4-demo.mp4`)은 proposal-outline § 3 의 6 segment 구성을 그대로 따른다. 모든 의료/금융/광고 디스클레이머는 **법무 스타일 점검(Day 3 EOD)** 을 통과한 최종 카피로 노출된다. mypy strict / ruff strict / pytest coverage ≥ 80% 는 W2/W3 와 동일하게 유지하되, **5.25 12:00 KST 코드 동결 이후의 코드 변경은 금지** (변경 시 시연 영상 재촬영 + AC 전수 재검증 트리거).

### 1.1 In Scope

- **Stage 2 질병 분류기 (`apps/ai-server`)**:
  - 1차 (MVP): PetBERT (HuggingFace) 베이스 + 시계열을 자연어 문장으로 직렬화("활동 30%↓, 심박 평균 10%↑, 식이량 20%↓ ...") 하여 fine-tune. fine-tune 자체는 **오프라인 1회 배치**(W4 Day 1 야간 1 epoch 또는 사전 W3 산출물 사용). cron/A/B 자동화는 out.
  - 2차 (PetBERT 라이선스/가용성 블록 시 fallback): Korean base LM(`klue/roberta-base` 등) 로 **zero-shot classification** + 큐레이션된 한국어 라벨 리스트(top-20 견 질병). HuggingFace `pipeline("zero-shot-classification")` 1줄 swap.
  - `POST /infer/disease` 로컬 AI 서버 엔드포인트. **mTLS + HMAC** 인증(spec 02 § 3.4). 5초 타임아웃. 타임아웃/에러 시 룰 기반 fallback (`action="observe"`, `top_diseases=[]`).
  - 출력 스키마: `{anomaly_score, top_diseases:[{label, prob, confidence_band:[lo,hi]}], action:"immediate"|"schedule"|"observe"}` (top-3).
- **MedicalBudget β 항 wiring (`apps/api`)**:
  - W3 의 `predict_budget()` 에서 `β term = 0` (mock) 으로 두었던 분기를 Stage 2 결과 (`top_diseases`) 와 정적 `disease_cost_factor` 테이블로 **실 계산**하도록 교체.
  - `disease_cost_factor` 정적 표 (top-20 라벨 × p50 비용 가중치) — `apps/api/app/services/disease_cost.py`.
  - `MedicalBudget.recompute(pet_id)` 가 최신 `Diagnosis.top_diseases` 를 읽어 β 항 반영, `drivers` 필드에 disease 기여도 명시.
- **Savings recommendation flow (`apps/api` + `apps/mobile`)**:
  - `GET /v1/finance/savings?monthly={amount}` → 큐레이션 정적 상품 1~3개 (KB펫적금·카카오뱅크 자유적금·토스뱅크 자유적금) — `apr/min_monthly/deeplink_url/badges` 포함. monthly 가 min_monthly 이상인 상품만 반환.
  - `POST /v1/finance/mock-enroll {savings_id, monthly}` → `MockSavingsContract(id, user_id, savings_id, monthly, fake_contract_id, enrolled_at, reminder_at)` 생성, 14일 후 리마인더 일정 RQ enqueue, 계약 상세 반환.
  - 모바일 홈 화면: 의료비 카드 *바로 아래* 적금 권장 카드 ("월 4.2만원 적금하면 충격 없이 대비할 수 있어요") + **3-button CTA** (외부 가입 / mock 가입 / 나중에).
  - 디스클레이머 배너: "본 서비스는 금융상품 자문이 아닙니다. PoC 시연 — 실제 적금이 아닙니다." (카드 푸터 의무 노출).
- **Donation campaign integration (`apps/api` + `apps/mobile`)**:
  - `GET /v1/donations/campaigns` → 정적 시드 3~5개 보호소 캠페인(이름·요약·이미지 URL·외부 redirect URL). 인앱 결제 없음.
  - `POST /v1/donations/redirect {campaign_id}` → 클릭 트래킹(`DonationClickLog`) + 외부 URL 반환.
  - 모바일 홈: 적금 카드 *바로 아래* 후원 카드 + "건강 마일리지 1,000원 후원" CTA (단순 외부 redirect).
- **E2E demo seed scenarios (`apps/api/seeds/demo_scenarios.py`)**:
  - 시나리오 A: 보리(시바, 4세, 기저없음) → 14일 health snapshot → anomaly 0.62 → top-disease "위장 트러블 12%" → MedicalBudget p50 32만 / p90 50만 → 권장 월 4.2만.
  - 시나리오 B: 시니어 푸들(11세, 신장질환) → anomaly 0.78 → top-disease "신장기능저하 18%" → p50 80만 / p90 130만 → 권장 월 11만.
  - CLI: `python -m app.seeds.demo_scenarios --reset` (멱등 — 기존 user/pet/health/diagnosis/budget/contract row 전부 삭제 후 재생성). 영상 촬영 1회 실행으로 모든 P0 화면 재현.
- **컴플라이언스 디스클레이머 final pass**:
  - 의료: "AI 추정치이며 수의사 상담을 대체하지 않습니다" — health/disease 카드 의무.
  - 금융: "금융상품 자문이 아니며 가입은 해당 금융사 안내에 따릅니다" — 적금 카드 의무.
  - 후원: "후원금은 외부 단체로 직접 전달됩니다" — 후원 카드 의무.
  - 광고성 노출 표기 (전자상거래법) — 적금 deeplink 버튼 옆 "광고" 배지 의무.
  - **Day 3 EOD 까지** PM/리드가 법무 스타일 1차 검수 완료 (자문 변호사 미확보 시 KB·토스 적금 약관 페이지 스타일 카피 미러링).
- **90초 시연 영상 (`.omc/research/w4-demo.mp4` + `docs/w4-demo-script.md`)**:
  - proposal-outline § 3 의 6 segment 그대로 (0:00 / 0:10 / 0:25 / 0:45 / 1:05 / 1:20).
  - 화면 캡처 + 한국어 보이스오버 + 자막. 출력 spec: 1920×1080 @ 30fps, h264, ≤ 50MB.
  - 스크립트는 `docs/w4-demo-script.md` 에 한국어로 사전 작성, Day 3 EOD 리허설 1회.

### 1.2 Out of Scope (본선 8.28 또는 Phase 2 이후)

- 실 오픈뱅킹 직접 연동 (사업자 등록 필요) — 외부 가입 deeplink 로 대체.
- Caretail 실 webhook (push) — W3 까지의 5분 폴링 유지, push 전환은 본선.
- Multi-pet · multi-species (고양이·소형동물) — 단일 견종 시연.
- B2B clinic SaaS — Phase 3.
- Stage 2 LoRA fine-tune 자동 cycle (cron, A/B test) — fine-tune 은 **오프라인 1회 배치**만, 자동화 없음.
- Apple Sign-In — 카카오 로그인만.
- 실 결제 모듈, BNPL, 보험 비교.

### 1.3 Constraints

- **5.25 12:00 KST 하드 코드 프리즈**. 그 이후 commit 금지(영상 재촬영 + AC 전수 재검증 비용). PM 이 main 브랜치 protection rule 활성화 (`require_pull_request_reviews=true, dismissals=admin-only`).
- 모든 P0 사용자 흐름은 `python -m app.seeds.demo_scenarios --reset` 한 줄로 재현 가능. 수동 setup 단계 0.
- mypy strict, ruff strict, pytest coverage ≥ 80% 유지 (W3 와 동일).
- 모든 디스클레이머 카피는 Day 3 EOD 까지 PM legal-style 1차 통과.
- 모바일 빌드는 Day 3 EOD 까지 iOS Simulator + Android Emulator 양쪽에서 release variant 빌드 통과.
- Day 4 (5.25) 는 **freeze + QA 회귀 + 영상 최종 컷 + 제출 패키지** 만. 신규 코드 머지 금지. 12:00 KST 이후로는 PR 머지 lock.
- 4–5인 팀 분담 (백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1). 5.24 일요일도 작업 가능. 일정상 W2/W3 보다 짧으므로 *Day 7 retrospective 같은 여유 없음*.

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `apps/ai-server` 가 `POST /infer/disease` 를 mTLS + HMAC 헤더로 받고, 정상 입력에 대해 `{anomaly_score, top_diseases:[{label, prob, confidence_band:[lo,hi]}], action}` 반환 (top-3) | `pytest apps/ai-server/tests/test_infer_disease.py::test_happy_path` (mTLS 클라이언트 cert + HMAC 서명) |
| AC2 | `/infer/disease` 5초 타임아웃 초과 시 cloud API 측 fallback 이 `action="observe"`, `top_diseases=[]` 으로 응답을 반환하고 에러 마스킹 | `pytest apps/api/tests/test_disease_client.py::test_timeout_fallback` (httpx mock, 6s sleep) |
| AC3 | `MedicalBudget.recompute(pet_id)` 가 최신 `Diagnosis.top_diseases` 의 prob 와 `disease_cost_factor` 가중치로 β 항을 산출하고, `drivers` 필드에 `["disease:신장기능저하:0.18"]` 형태 entry 포함 | `pytest apps/api/tests/test_medical_budget.py::test_beta_term_from_top_diseases` |
| AC4 | `GET /v1/finance/savings?monthly=42000` 가 큐레이션 상품 1~3개 반환, 각 row 에 `apr, min_monthly, deeplink_url, badges` 존재. monthly < min_monthly 인 상품은 제외 | `pytest apps/api/tests/test_savings.py::test_savings_filter_by_monthly` |
| AC5 | `POST /v1/finance/mock-enroll {savings_id, monthly:42000}` 가 `MockSavingsContract` 1 row 생성 + 14일 후 리마인더 RQ job enqueue + 계약 상세(`fake_contract_id` 포함) 반환 | `pytest ::test_mock_enroll_creates_contract_and_reminder` (fakeredis + RQ SimpleWorker) |
| AC6 | `GET /v1/donations/campaigns` 가 정적 시드 3~5개 캠페인 반환, `POST /v1/donations/redirect {campaign_id}` 가 `DonationClickLog` 1 row 적재 + 외부 url 반환 | `pytest apps/api/tests/test_donations.py::test_donation_click_log_and_redirect` |
| AC7 | `python -m app.seeds.demo_scenarios --reset` 1회 실행으로 시나리오 A·B 2종 (user, pet, 14일 health_snapshot, diagnosis, medical_budget, savings_recommendation cache) 결정적 적재. 재실행 결과가 byte-equal | `pytest apps/api/tests/test_demo_seed.py::test_seed_idempotent` (실행 2회 후 SELECT 비교) |
| AC8 | 모바일 홈 화면: 의료비 카드 → 적금 카드(3-CTA) → 후원 카드 순서로 렌더되며, 시나리오 A·B 양쪽 모두 90초 시연 영상에 발화 | `.omc/research/w4-demo.mp4` (1920×1080 @ 30fps, h264, ≤ 50MB) + `docs/w4-demo-script.md` |
| AC9 | 모든 디스클레이머(의료/금융/후원/광고성 표기) 가 모바일 4종 카드(헬스, 의료비, 적금, 후원)에 visible. PM legal-style 1차 검수 sign-off | `docs/w4-disclaimer-checklist.md` 체크리스트 9/9 + PM 서명 |
| AC10 | mypy 0 errors, ruff 0 errors, pytest coverage ≥ 80%, mobile typecheck 0 errors, iOS Simulator + Android Emulator release variant 빌드 통과 | CI green (`.github/workflows/api.yml`, `.github/workflows/mobile.yml`) + Day 3 EOD 양 OS 빌드 로그 첨부 |

> Done 임계: 10개 중 ≥ **9개** (W2/W3 보다 1단계 strict — final week).
> 미통과 1개는 5.25 09:00 KST 까지 보강 가능. 12:00 KST 코드 프리즈 이후는 docs/script 보강만 허용.

---

## 3. Implementation Steps (Day 단위)

### 3.1 Day 1 (5.22 금) — Stage 2 LM + /infer/disease 엔드포인트

> 가장 risky 한 작업을 1일차에 배치. W3 까지 mock 으로 두었던 disease 분기를 실 추론 경로로 교체.

#### 트랙 A · Stage 2 PetBERT serving (AI/infra)
- [ ] `apps/ai-server/app/models/disease_classifier.py`:
  - 1차 시도: `transformers.AutoModelForSequenceClassification.from_pretrained("petbert/...")`. 모델 가중치 로컬 캐시(`/var/cache/petfinect/models/`).
  - 라이선스/다운로드 블록 시 fallback: `transformers.pipeline("zero-shot-classification", model="klue/roberta-base")` + `apps/ai-server/app/labels/diseases_ko_top20.json` (위장 트러블, 신장기능저하, 슬개골탈구, 외이염, 치주염, 피부염, 심장사상충, 백내장, 관절염, 갑상선기능저하, 당뇨, 췌장염, 림프종, 비만, 결막염, 요로결석, 알러지성 피부염, 뇌수막염, 자궁축농증, 간기능저하).
  - `serialize_snapshots(snapshots, pet_meta) -> str` — 14일 시계열을 자연어 1문단으로 직렬화 ("활동 30% 감소, 평균 심박 10% 증가, 식이량 20% 감소, 4세 시바, 기저질환 없음").
  - `infer(snapshots, pet_meta) -> InferResult` — 모델 호출 + top-3 추출 + `confidence_band` (간이 bootstrap 또는 softmax variance).
- [ ] `apps/ai-server/app/api/infer.py`:
  - `POST /infer/disease` (FastAPI). request: `{pet_id, snapshots:[...], pet_meta:{breed,age,weight,conditions[]}}`. response: `{anomaly_score, top_diseases:[{label,prob,confidence_band:[lo,hi]}], action}`.
  - action 결정: `prob_top1 >= 0.5 → immediate`, `0.2 <= prob_top1 < 0.5 → schedule`, `else observe`.
  - 처리 시간 5초 초과 시 (asyncio.timeout) 503 + 룰 기반 응답 (`action="observe"`).
- [ ] mTLS + HMAC 인증:
  - `apps/ai-server/app/middleware/auth.py` — TLS client cert 검증 + `X-PetFinect-HMAC` 헤더(SHA256(body+ts+shared_secret)) 5분 윈도 검증.
  - `apps/ai-server/certs/` self-signed CA + server/client cert (개발용, gitignore).
- [ ] AC1 테스트: `apps/ai-server/tests/test_infer_disease.py::test_happy_path` (httpx + cert).

#### 트랙 B · Cloud → AI server client (backend lead)
- [ ] `apps/api/app/integrations/disease/__init__.py` — `DiseaseProvider` Protocol.
- [ ] `apps/api/app/integrations/disease/local.py` — `LocalAIDiseaseProvider`:
  - httpx AsyncClient + client cert (`settings.ai_server_client_cert`), HMAC 서명 헤더.
  - 5초 타임아웃, 1회 retry (jitter), 최종 실패 시 fallback `{anomaly_score: 0, top_diseases: [], action: "observe"}`.
- [ ] `apps/api/app/integrations/disease/mock.py` — 시나리오 A·B 결정적 응답 (시드 일치).
- [ ] `apps/api/app/integrations/disease/factory.py` — `APP_ENV != production and AI_SERVER_USE_MOCK == "1"` 시 mock.
- [ ] `apps/api/tests/test_disease_client.py` — AC2 (timeout fallback).

#### 트랙 C · MedicalBudget β term wiring (backend dev)
- [ ] `apps/api/app/services/disease_cost.py` — `disease_cost_factor: dict[str, float]` (top-20 라벨 × p50 비용 가중치, 출처 메모 `docs/data/disease-cost-source.md`).
- [ ] `apps/api/app/services/medical_budget.py`:
  - W3 의 `predict_budget(pet_id)` 에서 β=0 mock 분기 제거.
  - `β = Σ top_diseases[i].prob * disease_cost_factor[label]` 으로 교체.
  - `drivers` 필드에 `f"disease:{label}:{prob:.2f}"` entry 추가.
- [ ] `apps/api/tests/test_medical_budget.py::test_beta_term_from_top_diseases` — AC3.

#### 트랙 D · 시드 베이스라인 보강 (lead/PM)
- [ ] `apps/api/seeds/disease_baseline.py` — top-20 라벨 별 평균 진료비(원) 정적 표 시드. 출처 (KB펫금융보고서, 펫보험사 공시) `docs/data/disease-cost-source.md` 명시.

**Day 1 종료 조건**: AC1 + AC2 + AC3 통과. `apps/ai-server` 가 docker compose 로 띄워지고 cloud API 가 시나리오 A 입력으로 호출 시 결정적 응답.

---

### 3.2 Day 2 (5.23 토) — Savings + Donation API + 모바일 카드 UI

#### 트랙 A · Savings API + Mock Enroll (backend lead)
- [ ] `apps/api/app/models/savings_product.py` — W3 에서 모델만 있었다면 그대로, 없었다면 신규 (`id, provider_name, apr, min_monthly, deeplink_url, badges, region`).
- [ ] `apps/api/app/models/mock_savings_contract.py` 신규 — `id, user_id FK, savings_id FK, monthly, fake_contract_id (uuid4), enrolled_at, reminder_at`.
- [ ] `apps/api/seeds/savings_products.py` — KB펫적금/카카오뱅크 자유적금/토스뱅크 자유적금 3건 정적 시드 (apr·min_monthly·deeplink_url 출처 `docs/data/savings-source.md`).
- [ ] `apps/api/app/api/v1/finance.py`:
  - `GET /v1/finance/savings?monthly=` — monthly ≥ min_monthly 인 row 만 반환, apr DESC 정렬, top-3.
  - `POST /v1/finance/mock-enroll {savings_id, monthly}` — 계약 row + RQ enqueue (`reminders.savings_reminder(contract_id)` 14일 후) + 응답.
- [ ] `apps/api/app/workers/reminders.py` — `savings_reminder(contract_id)` 푸시 1건 발송 (W3 push provider 재사용).
- [ ] `alembic revision -m "0005_w4_finance_donation"` (mock_savings_contract + donation_click_log 동시 마이그).
- [ ] `apps/api/tests/test_savings.py` — AC4, AC5.

#### 트랙 B · Donation API (backend dev)
- [ ] `apps/api/app/models/donation_campaign.py` 신규 — `id, name, summary, image_url, redirect_url, region, source_org`.
- [ ] `apps/api/app/models/donation_click_log.py` 신규 — `id, user_id, campaign_id, clicked_at, ua, referer`.
- [ ] `apps/api/seeds/donation_campaigns.py` — 3~5건 정적 시드 (농림축산식품부 동물보호관리시스템 보호소 + 등록 NGO, 출처 `docs/data/donation-source.md`).
- [ ] `apps/api/app/api/v1/donations.py`:
  - `GET /v1/donations/campaigns` — 시드 row 전체 반환.
  - `POST /v1/donations/redirect {campaign_id}` — log 적재 + redirect_url 반환.
- [ ] `apps/api/tests/test_donations.py` — AC6.

#### 트랙 C · 모바일 홈 카드 3종 (mobile dev)
- [ ] `apps/mobile/src/components/MedicalBudgetCard.tsx` — W3 산출. drivers 필드에서 `disease:*` entry 가시화.
- [ ] `apps/mobile/src/components/SavingsCard.tsx` 신규:
  - props: `monthly: number`.
  - mount 시 `GET /v1/finance/savings?monthly=`. 1~3개 상품 horizontal scroll.
  - 각 상품 카드: provider · apr · min_monthly · badges · 3-button CTA(외부 가입 → `Linking.openURL(deeplink)` + 트래킹 ping / mock 가입 → `POST /v1/finance/mock-enroll` 후 success modal / 나중에 → dismiss).
  - 푸터 디스클레이머: "본 서비스는 금융상품 자문이 아닙니다. PoC 시연 — 실제 적금이 아닙니다." + "광고" 배지.
- [ ] `apps/mobile/src/components/DonationCard.tsx` 신규:
  - mount 시 `GET /v1/donations/campaigns`. 캠페인 1건 hero + 추가 carousel.
  - "건강 마일리지 1,000원 후원" CTA → `POST /v1/donations/redirect` 후 외부 URL open.
  - 푸터 디스클레이머: "후원금은 외부 단체로 직접 전달됩니다."
- [ ] `apps/mobile/app/(tabs)/index.tsx` — 카드 순서: 헬스 sparkline → 의료비 카드 → **적금 카드** → **후원 카드** → 캘린더 카드.
- [ ] `apps/mobile/src/api/{finance,donations}.ts` 신규.

#### 트랙 D · 디스클레이머 final pass 1차 (lead/PM)
- [ ] `docs/w4-disclaimer-checklist.md` 작성 — 9개 항목 체크리스트:
  - 헬스 카드: "AI 추정치 ..." 노출
  - 의료비 카드: "AI 추정치 ..." + "통계적 추정치 ..." 노출
  - 적금 카드: "금융상품 자문 ..." 노출
  - 적금 deeplink 버튼 옆: "광고" 배지
  - mock 가입 success modal: "PoC 시연 — 실제 적금이 아닙니다."
  - 후원 카드: "후원금은 외부 단체로 ..." 노출
  - 후원 redirect 직전 confirm: "외부 사이트로 이동합니다" alert
  - 푸시 알림 본문: "참고용 추정치, 의료 진단 아님"
  - 앱 about 페이지: 종합 디스클레이머 + 제3자 데이터 출처 표

**Day 2 종료 조건**: AC4 + AC5 + AC6 통과. 모바일 홈에서 카드 3종이 시각적으로 발화.

---

### 3.3 Day 3 (5.24 일) — E2E 시드 시나리오 + 모바일 빌드 + 디스클레이머 sign-off + 영상 1차 컷

> **Day 3 EOD 가 사실상의 코드 마감**. Day 4 는 freeze + 영상 + 제출.

#### 트랙 A · `demo_scenarios.py` 시드 (backend lead + AI/infra)
- [ ] `apps/api/seeds/demo_scenarios.py`:
  - argparse `--reset` 플래그 — 모든 demo user/pet/health/diagnosis/budget/contract/click_log row 삭제 후 재생성.
  - 시나리오 A: user `demo-a@petfinect.kr`, pet 보리(시바, 4세), 14일 health_snapshot (Day12~14 활동 30%↓, 심박 평균 10%↑, anomaly 0.62 산출 보장), diagnosis (top-disease "위장 트러블" prob 0.12), MedicalBudget(p50=320000, p90=500000, recommended_monthly=42000), savings 캐시.
  - 시나리오 B: user `demo-b@petfinect.kr`, pet 시니어 푸들(11세, 신장질환), 14일 health (anomaly 0.78), diagnosis (top-disease "신장기능저하" prob 0.18), MedicalBudget(p50=800000, p90=1300000, recommended_monthly=110000), savings 캐시.
  - 결정적: random seed 고정, ts 는 `--reset` 시점 기준 상대 (KST today-13d ~ today).
- [ ] `apps/api/tests/test_demo_seed.py::test_seed_idempotent` — 2회 실행 후 row 수·핵심 컬럼 hash 동일 → AC7.

#### 트랙 B · 모바일 release variant 빌드 + 양 OS 검증 (mobile dev)
- [ ] `pnpm -C apps/mobile prebuild` 후 iOS Simulator (`pnpm ios --release`) + Android Emulator (`pnpm android --release`) 빌드 → 양쪽에서 시나리오 A·B 로그인 → 카드 3종 렌더 캡처.
- [ ] 빌드 로그를 `.omc/research/w4-build-ios.log`, `w4-build-android.log` 에 첨부 (AC10 의 일부).

#### 트랙 C · 디스클레이머 PM legal-style sign-off (lead/PM)
- [ ] `docs/w4-disclaimer-checklist.md` 9/9 통과 + PM 서명(`signed_by`, `signed_at`).
- [ ] AC9 통과.

#### 트랙 D · 시연 영상 1차 컷 + 스크립트 (mobile dev + PM)
- [ ] `docs/w4-demo-script.md` 작성 — proposal-outline § 3 의 6 segment 한국어 보이스오버 스크립트 (segment 별 타이밍 + 자막 텍스트).
- [ ] 화면 캡처 도구(QuickTime + scrcpy 또는 Xcode Simulator screen recording) 로 6 segment 촬영 → 1차 편집 → `.omc/research/w4-demo-cut1.mp4` (rough cut, 1920×1080 @ 30fps).

**Day 3 종료 조건**: AC7 + AC9 통과. AC10 의 mobile 빌드 부분 통과. 시연 영상 1차 컷 존재. **Day 3 EOD = 코드 PR open 마지막 시점**.

---

### 3.4 Day 4 (5.25 월) — Freeze · QA 회귀 · 영상 최종 · 제출 패키지 (코드 동결)

> **신규 코드 머지 금지**. 12:00 KST 까지 모든 PR merge 종료. 이후는 docs/스크립트/영상/제출 자료만.

#### 09:00 ~ 12:00 — 최종 머지 + AC 전수 회귀
- [ ] 잔여 PR(있다면) 머지 → main brunch protection lock activate.
- [ ] CI green 확인 (api + mobile 양쪽 workflow).
- [ ] `python -m app.seeds.demo_scenarios --reset` → AC1~AC10 수동 회귀 (체크리스트 `docs/w4-final-qa-checklist.md`).
- [ ] AC 통과 < 9 → 미통과 항목을 docs 한정으로 보강(코드 변경 금지). docs/스크립트로 회피 가능한 경우만 통과 인정.

#### 12:00 — 코드 프리즈 (PR merge lock)
- [ ] PM 이 main 브랜치 protection rule 강화 (`require_admin=true`).
- [ ] 마지막 commit hash 를 `docs/w4-submission-manifest.md` 에 기록.

#### 12:00 ~ 16:00 — 시연 영상 최종 컷
- [ ] Day 3 1차 컷 + 보이스오버 더빙 (Korean TTS or 인력 1인 녹음) + 자막 + 디스클레이머 텍스트 오버레이.
- [ ] 출력: `.omc/research/w4-demo.mp4` (1920×1080 @ 30fps, h264, ≤ 50MB).
- [ ] AC8 통과 확인.

#### 16:00 ~ 17:00 — 제출 패키지
- [ ] `docs/w4-submission-manifest.md` 작성 (체크리스트 § 5 참조).
- [ ] 챌린지 포털 업로드 (영상 + 사업계획서 PDF + 팀 정보).
- [ ] **17:00 KST 마감 전 30분 여유 확보**.

---

## 4. Risks & Mitigations

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | PetBERT 다운로드/라이선스 블록 (HuggingFace 비공개 또는 한국어 미지원) | **高** | **高** | Day 1 09:00 시점에 1시간 spike → 블록 시 `klue/roberta-base` zero-shot 으로 즉시 swap. 두 경로 모두 `disease_classifier.py` 내 1줄 swap 으로 가능하게 사전 추상화. AC1 은 어느 경로든 통과. |
| R2 | mTLS + HMAC 셋업이 docker-compose 환경에서 self-signed cert 검증 실패 | 中 | 高 | self-signed CA 를 cloud API container 의 `SSL_CERT_FILE` 에 마운트, 개발용 cert 만료 90일 사전 발급. 실패 시 dev 환경 한정 `verify=False` + HMAC 만 검증으로 임시 폴백, 제출 후 본선까지 정식 cert 교체. |
| R3 | Day 4 12:00 코드 프리즈 후 critical bug 발견 (예: AC4 적금 카드 모바일 crash) | 中 | **高** | Day 3 EOD 까지 모바일 양 OS release variant 빌드 + AC1~AC10 dry-run 의무. Day 4 09:00 회귀에서 발견된 bug 만 12:00 전 hotfix PR 1개 허용 (PM + lead 양자 승인). |
| R4 | 디스클레이머 카피가 법무 검토 기준 미흡 (실제 변호사 자문 미확보) | 中 | 中 | KB·토스 적금 약관 페이지 카피 mirror + 광고성 노출 표기 (전자상거래법) 사전 점검 체크리스트 (`docs/w4-disclaimer-checklist.md` 9/9). 본선까지 변호사 자문 1회 확보. |
| R5 | 시연 영상 50MB cap 초과 (1920×1080 @ 30fps × 90초 + h264 기본 비트레이트) | 中 | 中 | h264 CRF 23~28 + 1pass 인코딩, 음성 192kbps AAC. 초과 시 720p downscale 우선, 그래도 초과면 80초로 트리밍 (segment 6 후원 컷을 정적 카드로 단축). |
| R6 | `demo_scenarios.py --reset` 가 운영 DB 에 잘못 실행될 위험 | 低 | **高** | CLI 진입부에 `if settings.app_env == "production": raise RuntimeError`. demo user email `*@petfinect.kr` 도메인만 삭제하도록 WHERE 절 강제. CI 에서도 DSN 환경변수 검증. |
| R7 | 5.24(일) 인력 부재 또는 5.25 새벽 야근 burnout 으로 마감 직전 머지 누락 | 中 | 中 | Day 3 EOD 가 사실상 마감으로 간주(Day 4 는 QA·영상·제출). 5.24 09:00 일일 standup 으로 잔여 task 가시화, 인력 부재 시 PM 이 트랙 swap. 5.25 새벽 작업 금지. |

---

## 5. Submission Packaging Checklist (Day 4 16:00 sealed)

- [ ] `.omc/research/w4-demo.mp4` (1920×1080 @ 30fps, h264, ≤ 50MB, 90초)
- [ ] 사업계획서 PDF (proposal-outline 12 슬라이드 기반, 5.24 EOD 디자인 1차 완성 가정)
- [ ] 팀 정보 (구성원·이메일·역할)
- [ ] GitHub repo URL (public 전환 또는 심사위원 access 권한)
- [ ] 마지막 commit hash + tag `v0.4.0-submission`
- [ ] `docs/w4-submission-manifest.md`:
  - 영상 파일명·해시 (sha256)
  - 시연 시드 명령 1줄 (`python -m app.seeds.demo_scenarios --reset`)
  - AC 통과표 (10개 중 X개)
  - 디스클레이머 카피 9개 final wording
  - 데이터 출처 (KB펫금융보고서, 농림축산식품부, 펫보험사 공시)
- [ ] CI green badge URL

---

## 6. Critical Path (Day 단위)

```
Day1 5.22 |■■■■■■■■|  Stage 2 LM + /infer/disease + β term     [AC1,2,3]
          |        |
Day2 5.23 |■■■■■■■■|  Savings + Donation API + 모바일 카드 3종  [AC4,5,6]
          |        |
Day3 5.24 |■■■■■■  |  demo_scenarios + 모바일 양 OS 빌드 + 디스클레이머 sign-off + 영상 1차 컷  [AC7,9, AC10 mobile 부분]
          |      ▼ |  ← Day3 EOD = 사실상의 코드 마감
Day4 5.25 |▣▣      |  09~12 최종 회귀 + 12:00 코드 프리즈
          |  ▣▣    |  12~16 시연 영상 최종 컷                   [AC8]
          |    ▣▣  |  16~17 제출 패키지 업로드
          |      ▼ |  ← 17:00 KST 마감
```

| 트랙 | Day1 | Day2 | Day3 | Day4 |
|---|---|---|---|---|
| A · Backend Lead | Stage 2 cloud client + β wiring | Savings API + mock-enroll | demo_scenarios | 회귀 + 프리즈 |
| B · Backend Dev | (지원) Stage 2 fallback 라벨 | Donation API + alembic | (지원) seed 검증 | 회귀 |
| C · AI/Infra | PetBERT serving + mTLS | (지원) AI 서버 docker compose | demo seed AI 분기 검증 | 영상 인코딩 |
| D · Mobile | (대기) | 카드 3종 UI | 양 OS release 빌드 + 영상 촬영 | 영상 최종 컷 |
| E · Lead/PM | 디스클레이머 초안 | 디스클레이머 1차 검수 | sign-off + 영상 스크립트 | 제출 패키지 |

---

## 7. Verification Steps

### 7.1 자동
```bash
cd apps/api
docker compose up -d postgres redis worker ai-server
uv pip install -e ".[dev]"
alembic upgrade head
python -m app.seeds.savings_products
python -m app.seeds.donation_campaigns
python -m app.seeds.disease_baseline
python -m app.seeds.demo_scenarios --reset
pytest -v --cov=app --cov-fail-under=80
ruff check .
mypy app                       # 0 errors
cd ../ai-server
pytest -v
cd ../../packages/shared-types
pnpm codegen
cd ../../apps/mobile
pnpm typecheck                 # AC10 모바일 부분
pnpm ios --release             # AC10 iOS 빌드
pnpm android --release         # AC10 Android 빌드
```

### 7.2 수동 (AC8, AC9)
1. `python -m app.seeds.demo_scenarios --reset` 1회 실행.
2. 모바일 시나리오 A 로그인 → 홈 → 의료비 카드(p50 32만 / p90 50만) → 적금 카드(월 4.2만 권장, 3-CTA) → mock 가입 → success modal 디스클레이머 → 후원 카드 → redirect alert.
3. 시나리오 B 동일 흐름 (월 11만 권장).
4. 90초 시연 영상 촬영 → `.omc/research/w4-demo.mp4`.
5. `docs/w4-disclaimer-checklist.md` 9/9 PM 서명 확인.

### 7.3 종료 점검 (Day 4 16:00)
- AC 통과 ≥ 9 → 제출 가능.
- AC 통과 < 9 → docs/script 보강만 시도 (코드 변경 금지). 그래도 미달 시 미달 사실을 `docs/w4-submission-manifest.md` 에 명시 후 제출 (silent omission 금지).

---

## 8. Team Allocation (4–5인)

| 트랙 | 인력 | 주요 산출 |
|---|---|---|
| Backend Lead | 1 | Stage 2 cloud client·MedicalBudget β·Savings API·demo_scenarios·회귀 |
| Backend Dev | 1 | Donation API·alembic·seed 검증·디스클레이머 wiring·회귀 |
| AI/Infra | 1 | PetBERT serving·mTLS·zero-shot fallback·ai-server docker compose·영상 인코딩 |
| Mobile Dev | 1 | 카드 3종 UI·양 OS release 빌드·영상 촬영·최종 컷 편집 |
| Lead/PM (5인 운영 시) | 1 | 디스클레이머 검수·시연 스크립트·제출 패키지·일정 게이트키핑 |

> 4인 운영 시 Lead/PM 역할을 Backend Lead 가 겸직, 영상 보이스오버 녹음은 Mobile Dev 가 담당.

---

## 9. File Map

```
apps/ai-server/
  app/api/infer.py                                        [new: POST /infer/disease]
  app/models/disease_classifier.py                        [new: PetBERT 또는 zero-shot fallback]
  app/middleware/auth.py                                  [new: mTLS + HMAC]
  app/labels/diseases_ko_top20.json                       [new]
  certs/                                                  [new: dev self-signed CA, gitignore]
  tests/test_infer_disease.py                             [new]

apps/api/
  alembic/versions/0005_w4_finance_donation.py            [new]
  app/models/{mock_savings_contract,donation_campaign,
              donation_click_log}.py                       [new]
  app/integrations/disease/{__init__,local,mock,factory}.py  [new]
  app/services/disease_cost.py                            [new]
  app/services/medical_budget.py                          [edit: β term wiring]
  app/api/v1/finance.py                                   [new: GET savings, POST mock-enroll]
  app/api/v1/donations.py                                 [new]
  app/workers/reminders.py                                [new: savings_reminder]
  seeds/disease_baseline.py                               [new]
  seeds/savings_products.py                               [new]
  seeds/donation_campaigns.py                             [new]
  seeds/demo_scenarios.py                                 [new: --reset CLI]
  tests/test_disease_client.py                            [new]
  tests/test_medical_budget.py                            [edit: β term 케이스]
  tests/test_savings.py                                   [new]
  tests/test_donations.py                                 [new]
  tests/test_demo_seed.py                                 [new]

apps/mobile/
  app/(tabs)/index.tsx                                    [edit: 카드 순서 헬스→의료비→적금→후원→캘린더]
  src/components/SavingsCard.tsx                          [new]
  src/components/DonationCard.tsx                         [new]
  src/components/MedicalBudgetCard.tsx                    [edit: drivers 가시화]
  src/api/{finance,donations}.ts                          [new]

packages/shared-types/                                    [edit: savings_product, mock_savings_contract,
                                                                 donation_campaign, disease_infer 추가]

docs/
  w4-demo-script.md                                       [new: 6 segment Korean]
  w4-disclaimer-checklist.md                              [new: 9 항목 + PM sign-off]
  w4-final-qa-checklist.md                                [new: Day 4 회귀]
  w4-submission-manifest.md                               [new: 제출 패키지]
  data/disease-cost-source.md                             [new]
  data/savings-source.md                                  [new]
  data/donation-source.md                                 [new]
  api/openapi-w4.json                                     [generated]

.omc/research/w4-demo.mp4                                 [new]
.omc/research/w4-demo-cut1.mp4                            [new, intermediate]
.omc/research/w4-build-ios.log                            [new]
.omc/research/w4-build-android.log                        [new]

docker-compose.yml                                        [edit: ai-server 서비스 추가]
```

---

## 10. Done Definition

- [ ] AC1~AC10 중 ≥ **9개** 통과 (final week strict).
- [ ] mypy 0 errors, ruff 0 errors, coverage ≥ 80% (AC10 backend 부분).
- [ ] Mobile typecheck 0 errors + iOS Simulator + Android Emulator release variant 빌드 통과 (AC10 mobile 부분).
- [ ] `python -m app.seeds.demo_scenarios --reset` 1줄로 시나리오 A·B 결정적 재현 (AC7).
- [ ] 90초 시연 영상 `.omc/research/w4-demo.mp4` (1920×1080 @ 30fps, h264, ≤ 50MB) (AC8).
- [ ] `docs/w4-disclaimer-checklist.md` 9/9 PM 서명 (AC9).
- [ ] `docs/w4-submission-manifest.md` 작성 + 5.25 17:00 KST 전 챌린지 포털 업로드 완료.
- [ ] 5.25 12:00 KST 코드 프리즈 — 그 이후 commit 0건.

---

## 11. Open Questions

1. **PetBERT 라이선스 / 한국어 지원** — Day 1 09:00 spike 결과에 따라 zero-shot fallback 전환. 두 경로 모두 시연에서는 결정적 응답이므로 시연 자체는 영향 없음. 본선까지 정식 모델 확정.
2. **mTLS cert 운영 환경 발급** — 개발용 self-signed 로 W4 마감, 본선까지 Let's Encrypt 또는 사내 CA 정식 발급 검토.
3. **시연 영상 보이스오버** — Korean TTS (예: ElevenLabs ko, 또는 네이버 클로바) vs 인력 1인 녹음. Day 3 EOD 까지 결정. 비용 제로 우선이면 인력 녹음.
4. **챌린지 포털 업로드 형식** — 영상이 mp4 직접 업로드인지 YouTube/Vimeo unlisted 링크인지 사전 확인 필요. 마감 48시간 전 (5.23 17:00) 까지 PM 확인 의무.
5. **demo_scenarios.py 결정성** — Stage 2 LM 추론 자체가 비결정적일 가능성 (softmax sampling). 시연용으로는 mock provider 강제 (`AI_SERVER_USE_MOCK=1`) 가 안전. 정식 추론 검증은 별도 트랙으로.
6. **5.25 17:00 마감 시각의 KST 정확성** — 챌린지 공지 재확인 필요. 24:00 일 가능성도 있으나 안전 마진으로 17:00 가정.
7. **legal-style 검수의 PM 단독 책임 한계** — 변호사 자문 미확보 상태에서 PM 검수만으로 디스클레이머 충분성을 보장할 수 없음. 본선까지 자문 1회 의무.

---

## 12. Changelog

- 2026-05-04 — 초안 작성. W3 산출물 (Stage 1 anomaly, MedicalBudget 1차 예측식 with β=0 mock, 병원 매칭, savings_product 모델) 가정. PetBERT 1순위 + zero-shot fallback. Day 4 (5.25) 코드 프리즈 12:00 KST, 마감 17:00 KST 가정. Done 임계 9/10 (W2/W3 보다 strict).
