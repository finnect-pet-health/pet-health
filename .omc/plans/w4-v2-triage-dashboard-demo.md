# W4-v2 Plan · 진단→진료과 트리아지 + 통합 건강 대시보드 + 시연/제출

> 기간: 2026-05-22(금) ~ 2026-05-25(월), **4일** · 4–5인 팀
> 상위 plan(SOT): `~/.claude/plans/jazzy-roaming-rose.md` (스코프 피벗 잠금)
> 선행 plan: `.omc/plans/w3-v2-multimodal-diagnosis-hospital.md` (이미지·오디오 진단 + 병원 매칭 1차)
> 참조 spec: `docs/specs/02-health-analysis.md`, `docs/specs/05-medical-budget-savings.md` (의료비/적금은 본선 보류, **placeholder 카드만**), `docs/proposal-outline.md` § 3 (90초 시연 컷 시트)
> 모드: **최종 제출 주차**. mock-first 유지(`AI_SERVER_USE_MOCK=1` 강제), Day 4 12:00 KST **HARD CODE FREEZE**.

**2026-05-07 결정**: 통합 대시보드 4 섹션 → **3 섹션** (이미지/오디오/식이). 옵셔널 워치 sparkline 섹션 삭제.

---

## 1. Requirements Summary

W4 종료(2026-05-25 17:00 KST 챌린지 포털 업로드) 시점에 다음이 동시에 성립해야 한다: (1) W3-v2 의 멀티모달 진단(이미지·오디오) 결과가 **진료과(피부과/안과/이비인후과/내과/응급)**로 자동 매핑되어 가까운 병원 3곳에 specialty match 표기가 노출되고, (2) 모바일에는 **이미지/오디오/식이 3섹션 + 의료비 placeholder 4번째 섹션**의 통합 건강 대시보드가 단일 화면에 렌더되며, (3) `AI_SERVER_USE_MOCK=1` 결정성 시드 시나리오 2종(보리·시니어 푸들)이 동일 입력에 동일 출력을 보장하고, (4) 90초 시연 영상(1920×1080@30fps h264 ≤50MB) + 사업계획서 PDF + GitHub 비공개 ZIP + 데모 시드 재현 스크립트가 패키지로 제출된다. 의료비 예측·적금 실 구현은 본선용 후속 plan으로 이월하고, W4 단계에서는 placeholder 카드 + 명시적 디스클레이머만 노출한다. 모든 진단 카드는 의료적 디스클레이머(`"AI 추정치이며 수의사 상담을 대체하지 않습니다"`)를 의무 노출하고, 금융 디스클레이머는 placeholder 카드에만 한정한다.

### 1.1 In Scope

- **Track A · 백엔드**: `apps/api/app/services/triage.py` (진단 라벨 → 진료과 + urgency 매핑), `apps/api/seeds/specialty_mapping.json` 룰 테이블, `GET /v1/hospitals/nearby?specialty=` specialty 필터 + `specialty_match`/`score` 응답 필드, 모든 진단·병원 응답에 `disclaimer: { medical, financial }` 객체 동봉.
- **Track B · 모바일**: `apps/mobile/app/(tabs)/dashboard.tsx` (또는 홈 화면 확장) — 3섹션(이미지·오디오·식이) + 의료비 placeholder 4섹션. 진단 카드 탭 → specialty 쿼리 자동 적용된 hospitals 화면 진입 흐름.
- **Track C · AI/인프라**: `apps/api/seeds/demo_scenarios.py --reset` CLI (Scenario A 보리/시바/4세, Scenario B 시니어 푸들/11세 신장 기저). vision/audio mock provider 의 file hash → 결정적 결과 매핑 테이블 강화. `AI_SERVER_USE_MOCK=1` 환경변수 강제 + 부재 시 명시적 에러.
- **Track D · 리드/PM**: `docs/w4-demo-script.md` 90초 컷 시트 (S6 슬라이드 § 3 6 segments, FIN-tech 부분을 멀티모달 데모로 대체), 시연 영상 1920×1080 @ 30fps h264 ≤ 50MB, 한국어 보이스오버, 의료/금융 디스클레이머 카피 검수, 제출 패키지 체크리스트, GitHub 비공개 저장소 ZIP, 사업계획서 PDF 최종본.
- **Day 4 (5.25 월) HARD FREEZE**: 12:00 KST 코드 동결, 이후 회귀 QA + 시연 영상 최종 편집 + 제출 패키지 검수 + 17:00 포털 업로드만 허용.

### 1.2 Out of Scope (본선 / Phase 2)

- **응급도(urgency) 분류 ML 모델** — W4-v2 에서는 룰 테이블의 enum 값만 표시(정보용), 실제 ML 분류는 Phase 2.
- **의료비 예측·적금 실 구현 + `MedicalBudget` 모델 + 통계 회귀 + 오픈뱅킹/적금 가입 페이지** — 본선용(5.26 이후 별도 plan), W4 는 placeholder 카드만.
- **B2B 동물병원 SaaS / 펫보험 비교 / BNPL 진료비 분할결제** — Phase 3.
- **실 결제 / 오픈뱅킹 직접 연동** — 시연 범위 외.
- **카카오맵 실제 길찾기 딥링크 PoC 이상의 확장** — W3-v2 산출(deeplink stub) 그대로 유지.
- **신규 모달리티(영상/IMU/홈캠 YOLO)** — Phase 2.
- **Caretail 워치 통합 일체** — 2026-05-07 결정으로 완전 제거. mock·real swap 모두 out of scope.

### 1.3 Constraints

- **Day 4 (5.25 월) 12:00 KST 코드 동결**. 12:00–17:00 사이 코드 변경 금지(예외: PM + 리드 양자 승인된 hotfix 1건만 11:00–12:00 한정).
- **Day 3 EOD 까지 양 OS dev build 통과 의무** (iOS Expo dev client + Android dev client). 실패 시 Day 4 freeze 가 깨짐 → 즉시 비상 회의.
- mypy strict 0 errors, ruff strict 0 errors, pytest coverage ≥ 80% **유지** (W3-v2 종료 시점 기준 회복 또는 동결값 유지).
- `AI_SERVER_USE_MOCK=1` **강제** — Real provider 경로는 W4 환경에서 호출 시 명시적 에러 발생. 시연 결정성 보장.
- **의료적 디스클레이머**(`"AI 추정치이며 수의사 상담을 대체하지 않습니다"`) — 모든 진단 카드(이미지·오디오·통합 대시보드) 의무. **앱 첫 진입 시 1회** `"본 서비스는 의료기기가 아닙니다"` 모달 의무.
- **금융 디스클레이머**는 의료비 placeholder 카드에만 표시(`"의료비 예측·적금은 본선 단계 공개 예정. 본 서비스는 금융상품이 아닙니다"`). 다른 화면에는 노출 금지.
- 4–5인 팀 분담 유지(백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1). **5.25 월요일은 전 인원 참석 의무** (제출 누락 방지).
- 시연 영상 보이스오버는 Day 2 1차 컷 단계에서 한국어 더빙 시작, Day 4 14:00 까지 자막 + 리믹스 완료.

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `apps/api/seeds/specialty_mapping.json` 이 W3-v2 라벨 카탈로그(`apps/api/seeds/disease_labels.json` — 4 region × 5 label = 20 + 5 audio cat) 100% 커버, 각 라벨에 `specialty: enum('피부과','안과','이비인후과','내과','응급')` + `urgency: enum('routine','soon','urgent','emergency')` 매핑 존재 | `pytest apps/api/tests/test_triage.py::test_specialty_mapping_full_coverage` |
| AC2 | `triage(diagnosis_event_id)` 가 image/audio top-3 라벨 입력에 대해 `{ specialties: list[str], urgency: enum }` 결정적 반환 (top-1 specialty 우선, urgency 는 max severity) | `pytest ::test_triage_deterministic_for_demo_scenarios` |
| AC3 | `GET /v1/hospitals/nearby?lat=&lng=&specialty=피부과` 응답이 specialty 일치 병원 우선 정렬 + 각 항목에 `specialty_match: bool` + `score: float (0..1)` 포함 (score = `0.5*distance_norm + 0.3*specialty_match + 0.2*open_now`) | `pytest apps/api/tests/test_hospitals.py::test_specialty_filter_score` |
| AC4 | 모든 진단·병원 응답이 `disclaimer: { medical: str, financial: str }` 객체 동봉(빈 문자열 금지). budget placeholder 응답에는 financial 디스클레이머가 본선 보류 문구 포함 | `pytest ::test_disclaimer_envelope_present` (파라미터화 테스트로 ≥ 6 엔드포인트 검증) |
| AC5 | `python -m app.seeds.demo_scenarios --reset` 실행 시 Scenario A(보리·피부 사진→피부염 의심 12% + 식이 정상) + Scenario B(시니어 푸들·기침→이상 호흡음 0.62 + 식이 처방식) 두 시나리오가 멱등적으로 재현. 양 시나리오 모두 워치 데이터 없음 | 셸 스크립트 2회 실행 → DB diff 0, fixture json 파일 hash 일치 |
| AC6 | vision/audio mock provider 가 동일 file hash 입력에 대해 동일 top-3 라벨 + confidence 반환 (1000회 반복 테스트, drift 0%) | `pytest apps/api/tests/test_mock_determinism.py::test_vision_audio_mock_deterministic` |
| AC7 | 모바일 통합 대시보드(`apps/mobile/app/(tabs)/dashboard.tsx`)가 3섹션(이미지·오디오·식이) + 의료비 placeholder 4섹션을 단일 스크롤뷰로 렌더 | 시연 영상 + `pnpm -C apps/mobile test` UI snapshot |
| AC8 | 진단 결과 카드 하단의 "이 증상에 어울리는 가까운 병원 →" 버튼 탭 시 `/hospitals?specialty={매핑값}` 으로 라우팅 + specialty 필터 자동 적용된 결과 노출 | E2E (Maestro 또는 수동 시나리오 실행 영상) |
| AC9 | 앱 첫 진입 시 `"본 서비스는 의료기기가 아닙니다"` 모달 1회 노출 + 모든 진단 카드에 의료적 디스클레이머 텍스트 노출 + 금융 디스클레이머는 의료비 placeholder 카드에만 노출 | `pnpm -C apps/mobile test` (정적 텍스트 검색) + 시연 영상 |
| AC10 | `docs/w4-demo-script.md` 6 segment 컷 시트 + 90초 시연 영상 mp4 (1920×1080 @ 30fps, h264, ≤ 50MB, 한국어 보이스오버) `.omc/research/w4-demo-final.mp4` 산출 | `ffprobe` 메타데이터 검사 + 파일 크기 + 재생 시간 89~91초 |
| AC11 | 제출 패키지 4종(시연 영상 mp4, 사업계획서 PDF, GitHub 비공개 저장소 ZIP, 데모 시드 재현 스크립트 README) 이 `submission/` 폴더에 모이고 `submission/CHECKLIST.md` 가 모든 항목 체크 | Day 4 16:00 PM 검수 게이트 통과 + 17:00 포털 업로드 영수증 |
| AC12 | mypy strict 0 errors, ruff strict 0 errors, pytest coverage ≥ 80%, `pnpm -C apps/mobile typecheck` 0 errors, **양 OS(iOS dev client + Android dev client) 빌드 통과** Day 3 EOD | CI 로그 (`.github/workflows/api.yml`, `mobile.yml`) green + EAS Build 성공 링크 |

> **Done 임계: 12개 중 ≥ 9개 통과** (final week strict). 미통과는 Day 4 hotfix 슬롯(11:00–12:00)에서만 1건 보강 가능 + 본선 일정으로 이월. AC10/AC11/AC12 는 제출에 직결되므로 **반드시 통과** 권장 가중.

---

## 3. Implementation Steps (Day 단위)

### 3.1 Day 1 (5.22 금) — Triage 서비스 + 매핑 테이블 + 대시보드 1차 + demo_scenarios

> 4 트랙 동시 가동. 백엔드 트랙은 triage 코어, 모바일은 대시보드 골격, AI/인프라는 mock 결정성 강화 + 시드 시나리오, 리드/PM 은 컷 시트 초안.

#### 트랙 A · Triage 서비스 + 매핑 테이블 (Backend Lead)
- [ ] `apps/api/seeds/specialty_mapping.json` 신규 — W3-v2 라벨 카탈로그 전수 매핑.
  - 스키마: `{ "label": "skin_dermatitis", "specialty": "피부과", "urgency": "soon", "ko_name": "피부염" }`
  - 5 진료과 enum + 4 urgency enum 고정. 매핑 누락 라벨 발견 시 PR 리뷰에서 차단.
- [ ] `apps/api/app/services/triage.py` 신규:
  ```python
  class TriageResult(BaseModel):
      specialties: list[str]   # top-3 라벨에서 도출, 중복 제거 + 우선순위 정렬
      urgency: Urgency         # max severity across top-3
      rationale: str           # 디버깅용
  def triage(diagnosis_event_id: UUID) -> TriageResult: ...
  ```
- [ ] `apps/api/app/api/v1/diagnose.py` 응답에 `triage: TriageResult` 필드 추가 (W3-v2 응답 envelope 확장).
- [ ] `apps/api/tests/test_triage.py` — AC1, AC2.

#### 트랙 B · 통합 대시보드 3섹션 + placeholder (Mobile Dev)
- [ ] `apps/mobile/app/(tabs)/dashboard.tsx` 신규 (또는 기존 home 확장):
  - 섹션 1: 이미지 진단 카드 — 최근 1건 미니 미리보기 + "새로 촬영" 버튼.
  - 섹션 2: 오디오 진단 카드 — 최근 1건 spectrogram thumbnail + "녹음" 버튼.
  - 섹션 3: 식이 관리 카드 — 오늘 칼로리 도넛 + 사료 종류 분포(파이).
  - 섹션 4: 의료비 placeholder — `"의료비 예측 + 적금 권장은 본선 단계 공개 예정"` + 금융 디스클레이머.
- [ ] `apps/mobile/src/components/dashboard/{ImageDiagnosisCard,AudioDiagnosisCard,DietCard,BudgetPlaceholderCard}.tsx` 신규.
- [ ] `apps/mobile/src/api/dashboard.ts` — `GET /v1/pets/{id}/dashboard` aggregator (백엔드 보조).

#### 트랙 C · demo_scenarios.py + Mock 결정성 강화 (AI/Infra)
- [ ] `apps/api/seeds/demo_scenarios.py` 신규:
  - CLI: `python -m app.seeds.demo_scenarios --reset`
  - Scenario A: `pet=보리(시바·4세·기저없음)`, image upload(피부 사진 fixture) → triage(피부과·routine), diet(정상 칼로리 7일). 워치 데이터 없음.
  - Scenario B: `pet=시니어푸들(11세·신장 기저)`, audio upload(기침 음성 fixture) → triage(이비인후과·soon, urgency 최대), diet(처방식). 기침 음성 → 이상 호흡음 0.62 + 식이 처방식. 워치 데이터 없음.
  - 멱등성: 기존 데이터 truncate → 재삽입.
- [ ] `apps/api/app/integrations/vision/mock.py` + `apps/api/app/integrations/audio/mock.py` — file hash → 결정적 결과 매핑 테이블 강화. `sha256(file_bytes)[:8]` → fixed top-3 라벨 + confidence 매핑 dict 도입.
- [ ] `apps/api/app/core/config.py` — `AI_SERVER_USE_MOCK` 환경변수 부재 시 startup 에러(W4 환경 강제).
- [ ] `apps/api/tests/test_mock_determinism.py` — AC6.

#### 트랙 D · 90초 컷 시트 초안 + 디스클레이머 카피 (Lead/PM)
- [ ] `docs/w4-demo-script.md` 1차 (Day 1 EOD):
  - 6 segments (proposal-outline § 3 기반, FIN-tech 자리 → 멀티모달, 워치 세그먼트 제거):
    - 0:00–0:10 표지 + 문제 통계 (반려동물 의료비 부담 + 정보 비대칭)
    - 0:10–0:25 카카오 로그인 + 가족 초대
    - 0:25–0:45 카메라 촬영 + 음성 녹음 → AI 진단 결과 (이미지 카드 + 오디오 카드)
    - 0:45–1:05 진단 → 진료과 매칭된 병원 추천 (specialty_match 강조)
    - 1:05–1:20 식이 관리 카드 + 사료 종류별 영향 (대시보드 3섹션 시연)
    - 1:20–1:30 의료비/적금 placeholder + 본선 공개 + 슬로건
- [ ] `docs/copy/disclaimers.md` 신규 — 의료/금융 디스클레이머 카피 잠금.

**Day 1 종료 조건**: AC1, AC2, AC5(구현), AC6 통과. 모바일 대시보드 화면이 4섹션 골격으로 렌더(데이터 없어도 빈 카드 OK).

---

### 3.2 Day 2 (5.23 토) — 진료과↔병원 통합 + 디스클레이머 카피 적용 + 시연 영상 1차 컷

#### 트랙 A · `/v1/hospitals/nearby?specialty=` + 디스클레이머 envelope (Backend Lead + Backend Dev)
- [ ] `apps/api/app/api/v1/hospitals.py` 수정:
  - `GET /v1/hospitals/nearby?lat=&lng=&specialty=&radius_km=&limit=` — specialty 파라미터 옵셔널.
  - 응답 항목: 기존 + `specialty_match: bool` + `score: float`.
  - 정렬: `score DESC` (가중치 distance 0.5 / specialty 0.3 / open_now 0.2).
- [ ] `apps/api/app/services/hospital_match.py` 신규 (또는 기존 service 확장) — score 계산.
- [ ] `apps/api/app/middlewares/disclaimer.py` 신규 — 진단/병원/budget placeholder 응답 envelope 에 `disclaimer` 자동 부착(라우터 데코레이터 또는 response_model_serializer).
  - medical: `"AI 추정치이며 수의사 상담을 대체하지 않습니다."`
  - financial: budget 응답에는 본선 보류 문구, 그 외엔 빈 객체 또는 omit.
- [ ] `apps/api/tests/test_hospitals.py` — AC3.
- [ ] `apps/api/tests/test_disclaimer_envelope.py` — AC4 (파라미터화).

#### 트랙 B · 진단 → 병원 안내 흐름 + 디스클레이머 UI (Mobile Dev)
- [ ] `apps/mobile/app/diagnose/result.tsx` (W3-v2 산출) 하단에 `"이 증상에 어울리는 가까운 병원 →"` 버튼 추가 + tap → `router.push({ pathname: '/hospitals', params: { specialty } })`.
- [ ] `apps/mobile/app/(tabs)/hospitals.tsx` — search params 의 specialty 자동 적용.
- [ ] `apps/mobile/src/components/MedicalDisclaimer.tsx` — 모든 진단 카드 푸터에 1줄 노출.
- [ ] `apps/mobile/app/_layout.tsx` 진입 시점에 `"본 서비스는 의료기기가 아닙니다"` 모달 1회(AsyncStorage flag `medical_modal_seen=true`).
- [ ] `apps/mobile/src/components/dashboard/BudgetPlaceholderCard.tsx` 에 금융 디스클레이머 잠금.
- [ ] AC8, AC9.

#### 트랙 C · 시연 시나리오 fixture 확정 + AI mock 결정성 회귀 (AI/Infra)
- [ ] `apps/api/tests/fixtures/demo/scenario_a/` (보리 피부 사진 1장, jpg) + `scenario_b/` (시니어 푸들 기침 wav).
- [ ] vision/audio mock 의 hash → 결정 결과 매핑 테이블에 fixture hash 등록.
- [ ] `python -m app.seeds.demo_scenarios --reset` 1000회 반복 회귀 테스트(CI nightly job, 본 W4 에서는 100회로 축소).

#### 트랙 D · 시연 영상 1차 컷 + 보이스오버 1차 (Lead/PM)
- [ ] iOS Expo dev client 또는 Android dev client 에서 6 segment 화면 녹화 (OBS or expo screen record).
- [ ] 한국어 보이스오버 1차 (PM 가성 또는 TTS 후 검수).
- [ ] `.omc/research/w4-demo-cut1.mp4` 산출 (편집 미완 OK).
- [ ] 디스클레이머 카피 최종본 검수(법무 자문 부재 → PM 자체 점검 + 자문 수의사 1인 검토 의뢰).

**Day 2 종료 조건**: AC3, AC4, AC8, AC9 통과. 시연 영상 1차 컷 존재 (편집 미완 OK).

---

### 3.3 Day 3 (5.24 일) — E2E 검증 + 양 OS 빌드 통과 + 시연 영상 2차 컷

> **Day 3 EOD 까지 양 OS dev build 통과 의무**. 신규 기능 코드 동결은 Day 3 18:00 PM. 이후 18:00–24:00 은 빌드/QA/영상 only.

#### 트랙 A · E2E 검증 + 회귀 (Backend Lead + Backend Dev)
- [ ] AC1~AC6 + AC12 일괄 실행 + 통과 확인.
- [ ] OpenAPI export → `docs/api/openapi-w4.json`. shared-types codegen 재실행.
- [ ] `apps/api/tests/test_e2e_demo_scenarios.py` 신규 — Scenario A + B 풀 흐름(login → upload → triage → hospitals) 통합 테스트.

#### 트랙 B · 양 OS dev build (Mobile Dev)
- [ ] `eas build --profile development --platform ios` + `--platform android` 양쪽 빌드.
- [ ] 인증서/keystore 사전 셋업 확인 (Day 2 까지 완료 권장, Day 3 fallback).
- [ ] dev client 설치 → Scenario A·B 수동 시연 1회씩 → 영상 녹화 백업.
- [ ] 빌드 실패 시 Day 3 18:00 비상 회의 → Expo Go fallback 결정 (단 시연 품질 저하).
- [ ] AC12 통과.

#### 트랙 C · demo_scenarios 영상 녹화 백업 + sentry 비활성 (AI/Infra)
- [ ] 시연 영상 backup 녹화 (mock 결정성 보장된 환경) — Day 4 hotfix 시 데이터 깨짐 방지용.
- [ ] sentry/telemetry 비활성 (시연 영상에 외부 호출 흔적 제거).

#### 트랙 D · 시연 영상 2차 컷 + 사업계획서 PDF 최종본 (Lead/PM)
- [ ] 보이스오버 + 자막 입력 + 컷 편집 → `.omc/research/w4-demo-cut2.mp4`.
- [ ] 사업계획서 PDF 최종본(`docs/proposal-final.pdf` 또는 `submission/PetFinect-Proposal.pdf`) 작성:
  - proposal-outline 12 슬라이드 → 슬라이드 8/9 (AI 모델·핀테크) 부분에 "본선 단계 부활" 명시.
- [ ] 제출 패키지 폴더 `submission/` 초기화 + `CHECKLIST.md` 작성:
  - [ ] 시연 영상 mp4 (≤ 50MB)
  - [ ] 사업계획서 PDF
  - [ ] GitHub 비공개 저장소 ZIP (Day 4 freeze 후 생성)
  - [ ] 데모 시드 재현 스크립트 README

**Day 3 종료 조건**: AC10(2차 컷) + AC12 통과, AC11 의 4종 중 3종 준비(GitHub ZIP만 Day 4 생성). 양 OS dev build 모두 성공.

---

### 3.4 Day 4 (5.25 월) — HARD FREEZE + 회귀 QA + 시연 영상 최종 + 제출

> **시간 단위 일정**. 12:00 KST 코드 동결. 17:00 포털 업로드.

| 시간 (KST) | 활동 | 책임 | 산출 |
|---|---|---|---|
| 09:00–11:00 | 회귀 QA — AC1~AC12 dry-run 2회 (mock 환경 + 실제 dev build) | Backend Lead + Mobile Dev + AI/Infra | `submission/qa-report.md` |
| 11:00–12:00 | hotfix 슬롯 — **1건만** 허용, PM + Backend Lead **양자 승인** 의무 | All | hotfix PR(승인된 경우) 또는 skip |
| **12:00** | **HARD CODE FREEZE** — git tag `submission-2026-05-25` + 모든 브랜치 보호 | Lead/PM | git tag 생성 |
| 12:00–14:00 | 시연 영상 최종 편집 — 보이스오버 리믹스 + 자막 타이밍 보정 + intro/outro 페이드 | Lead/PM + Mobile Dev (영상 컷 보조) | `submission/w4-demo-final.mp4` |
| 14:00–15:00 | 자막 한국어 검수(맞춤법·디스클레이머 표기) + 1920×1080@30fps h264 ≤ 50MB 인코딩 검증 | Lead/PM | `ffprobe` 결과 첨부 |
| 15:00–16:00 | GitHub 비공개 저장소 ZIP 생성 + 데모 시드 재현 README 최종본 + `submission/` 폴더 정리 | Backend Lead + Lead/PM | `submission.zip` |
| 16:00–17:00 | 제출 패키지 검수 게이트 — `submission/CHECKLIST.md` 100% 체크 + 4종 파일 존재 + ffprobe + PDF 페이지 수 확인 | All (전 인원) | 검수 통과 영수증 |
| 17:00 | **챌린지 포털 업로드** | Lead/PM | 업로드 confirmation 스크린샷 → `submission/upload-receipt.png` |

#### 트랙별 책임
- **Track A (Backend)**: 09:00–11:00 회귀 QA 주도, 11:00–12:00 hotfix 발생 시 PR 작성. 12:00 이후 코드 변경 금지.
- **Track B (Mobile)**: 09:00–11:00 dev build 실시연 2회(Scenario A + B), 12:00–14:00 영상 컷 보조, 16:00 검수 참여.
- **Track C (AI/Infra)**: 09:00–11:00 mock 결정성 dry-run 1000회 회귀, 12:00 이후 ZIP 생성 보조.
- **Track D (Lead/PM)**: 전 시간 진행, 12:00–17:00 영상 편집 + 패키지 작성 + 업로드.

**Day 4 종료 조건**: AC10, AC11 통과 + 17:00 포털 업로드 영수증 수령.

---

## 4. Parallel Tracks A/B/C/D Mapping

| 트랙 | 인력 | Day 1 | Day 2 | Day 3 | Day 4 |
|---|---|---|---|---|---|
| **A · 백엔드** | 2명 (Lead + Dev) | triage 서비스 + 매핑 JSON + diagnose 응답 envelope | hospitals specialty 필터 + score + disclaimer middleware | E2E 통합 테스트 + OpenAPI export + shared-types codegen | 회귀 QA 주도 + hotfix 작성 (12:00 freeze) |
| **B · 모바일** | 1명 | 대시보드 3섹션 + placeholder 카드 골격 | 진단→병원 라우팅 + 디스클레이머 모달/카피 + UI snapshot | EAS dev build 양 OS + 백업 영상 녹화 | 실시연 dry-run + 영상 컷 보조 + 검수 |
| **C · AI/Infra** | 1명 | demo_scenarios.py + mock hash 매핑 + AI_SERVER_USE_MOCK 강제 | fixture 확정 + 결정성 회귀 100회 | sentry/telemetry 비활성 + backup 녹화 | mock 결정성 dry-run 1000회 + ZIP 보조 |
| **D · 리드/PM** | 1명 | 컷 시트 초안 + 디스클레이머 카피 잠금 | 1차 컷 + 보이스오버 1차 | 2차 컷 + 자막 + 사업계획서 PDF + 패키지 폴더 초기화 | 영상 최종 편집 + GitHub ZIP + 검수 + 17:00 업로드 |

---

## 5. Risks & Mitigations

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | **시연 영상 보이스오버 지연** (PM 가성 녹음 시간 부족 또는 TTS 품질 미달) | 中 | 高 | Day 1 EOD 까지 컷 시트 잠금, Day 2 1차 보이스오버 의무. 자체 가성 실패 시 commercial TTS(Naver Clova or 네이버 TTS) 1시간 내 fallback. Day 3 까지 2차 컷 완성, Day 4 14:00 까지 자막만 보정. |
| R2 | **Mock 결정성 깨짐** (file hash 충돌 또는 라이브러리 비결정성) | 中 | 高 | `AI_SERVER_USE_MOCK=1` 강제 + hash → 매핑 dict 명시적 등록. Day 1 EOD AC6 통과 의무. Day 2 회귀 테스트 100회 이상. 시연 영상 backup 녹화(Day 3) 로 라이브 시연 실패 대비. |
| R3 | **양 OS dev build 실패** (인증서 만료, EAS 큐 적체, 빌드 시간 초과) | 中 | 高 | Day 2 까지 인증서/keystore 사전 셋업 완료. Day 3 EOD 까지 양 OS 통과 의무. 실패 시 Expo Go fallback (시연 품질 저하 감수) + backup 녹화 영상으로 시연 대체. |
| R4 | **Day 4 12:00 freeze 직전 버그 발견** | 高 | 中 | hotfix 슬롯 11:00–12:00 1건만 허용 + 양자 승인. 그 외는 본선 이월. AC 통과 9/12 임계로 일부 결함 허용. |
| R5 | **specialty 매핑 누락 라벨** (W3-v2 라벨 변경/추가가 W4 시작 시 반영 안 됨) | 中 | 中 | Day 1 AC1 (커버리지 100% 강제) 테스트. W3-v2 종료 직후 라벨 catalog snapshot → W4 매핑 JSON 생성 자동화 스크립트(있으면 사용). 누락 발견 시 default specialty="내과" + urgency="routine" 룰 fallback. |
| R6 | **디스클레이머 누락** (특정 화면/응답에서 envelope 미부착으로 컴플라이언스 실수) | 低 | 高 | middleware 자동 부착(라우터별 명시 X) + AC4 파라미터화 테스트로 ≥ 6 엔드포인트 강제 검증. UI 정적 텍스트 검색 테스트(AC9). 의료기기 모달 첫 진입 1회 강제. |
| R7 | **제출 패키지 50MB 초과** (시연 영상 인코딩 미스로 용량 폭증) | 中 | 中 | h264 + CRF 23 + 1920×1080 30fps 표준 프리셋 사전 검증. ffprobe + 파일 크기 게이트(Day 4 14:00). 초과 시 720p 다운스케일 또는 비트레이트 조정 fallback 1시간 슬롯 확보. |

---

## 6. Submission Packaging Checklist (frozen for Day 4 morning)

> Day 3 EOD 까지 `submission/CHECKLIST.md` 와 폴더 구조가 frozen 되어야 함. Day 4 는 채우기만 진행.

### 6.1 필수 산출물

- [ ] `submission/w4-demo-final.mp4` — 1920×1080 @ 30fps, h264, ≤ 50MB, 89~91초, 한국어 보이스오버 + 자막
- [ ] `submission/PetFinect-Proposal.pdf` — 사업계획서 12 슬라이드, S9(핀테크) "본선 부활" 명시
- [ ] `submission/petfinect-source.zip` — GitHub 비공개 저장소 zip (Day 4 12:00 freeze 시점 git archive)
- [ ] `submission/README.md` — 데모 시드 재현 스크립트 가이드:
  - `git clone <private-repo>`
  - `cp .env.example .env && sed -i 's/^AI_SERVER_USE_MOCK=.*/AI_SERVER_USE_MOCK=1/' .env`
  - `docker compose up -d postgres redis`
  - `cd apps/api && uv pip install -e ".[dev]" && alembic upgrade head`
  - `python -m app.seeds.demo_scenarios --reset`
  - `pnpm -C apps/mobile start` → Scenario A 시연 → Scenario B 시연
- [ ] `submission/CHECKLIST.md` — 본 체크리스트 자체
- [ ] `submission/qa-report.md` — Day 4 09:00–11:00 회귀 QA 결과
- [ ] `submission/upload-receipt.png` — 17:00 포털 업로드 confirmation

### 6.2 검수 게이트 (Day 4 16:00–17:00)

- [ ] `ffprobe submission/w4-demo-final.mp4` — codec h264, resolution 1920×1080, fps 30, duration 89~91s
- [ ] `du -sh submission/w4-demo-final.mp4` — ≤ 50MB
- [ ] `pdfinfo submission/PetFinect-Proposal.pdf` — pages 12 (또는 최종 슬라이드 수)
- [ ] `unzip -l submission/petfinect-source.zip | head` — 최상위 디렉토리 존재 확인
- [ ] 본 CHECKLIST 의 모든 체크박스 체크
- [ ] 4–5명 전원 sign-off

---

## 7. Critical-Path Bar Chart (ASCII)

```
                            Day 1 (5.22 금)        Day 2 (5.23 토)        Day 3 (5.24 일)        Day 4 (5.25 월) FREEZE
                            ─────────────────      ─────────────────      ─────────────────      ─────────────────
A · Backend (triage/hosp)   [████ triage+map  ]    [████ hosp+disc  ]     [██ E2E/openapi  ]     [██ QA] [-FREEZE-]
B · Mobile (dashboard)      [████ 4-section UI]    [████ flow+disc  ]     [████ EAS dev    ]     [██ dryrun] [---]
C · AI/Infra (demo seeds)   [████ scenarios   ]    [██ fixture conf ]     [██ backup rec   ]     [█ regress] [---]
D · Lead/PM (video/pkg)     [██ cut sheet     ]    [████ cut1+VO    ]     [████ cut2+PDF   ]     [████ FINAL EDIT + UPLOAD]
                                                                                                  09 11 12  14 15 16 17
                                                                                                  QA HF FZ ED EN CK UP
                                                                          Day 3 EOD ↑                                ↑
                                                                          양 OS dev build 통과                    포털 업로드
```

**Critical Path**: Day 1 triage 매핑 → Day 2 hospitals specialty + 디스클레이머 → Day 3 EAS 양 OS build + 영상 2차 컷 → Day 4 12:00 freeze → 17:00 업로드.

**가장 위험한 의존성**: Day 3 EAS dev build (R3) → 실패 시 Day 4 시연 영상 backup 녹화 fallback 필수.

---

## 8. Verification Steps

### 8.1 자동
```bash
cd /home/hidi/dev/health_pet/apps/api
export AI_SERVER_USE_MOCK=1
docker compose up -d postgres redis
uv pip install -e ".[dev]"
alembic upgrade head
python -m app.seeds.demo_scenarios --reset
pytest -v --cov=app --cov-fail-under=80 \
  tests/test_triage.py tests/test_hospitals.py \
  tests/test_disclaimer_envelope.py tests/test_mock_determinism.py \
  tests/test_e2e_demo_scenarios.py
ruff check .
mypy app
cd ../../packages/shared-types && pnpm codegen
cd ../../apps/mobile && pnpm typecheck && pnpm test
```

### 8.2 EAS 양 OS dev build (Day 3 EOD)
```bash
cd /home/hidi/dev/health_pet/apps/mobile
eas build --profile development --platform ios --non-interactive
eas build --profile development --platform android --non-interactive
# 양쪽 모두 success 확인 후 dev client 설치 → Scenario A/B 수동 시연
```

### 8.3 시연 영상 검증 (Day 4 14:00)
```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,codec_name,duration \
  -of default=noprint_wrappers=1 submission/w4-demo-final.mp4
# 기대: codec_name=h264, width=1920, height=1080, r_frame_rate=30/1, duration=89..91
du -sh submission/w4-demo-final.mp4   # ≤ 50M
```

### 8.4 제출 게이트 (Day 4 16:00)
- AC1~AC12 통과 ≥ 9/12 확인.
- `submission/CHECKLIST.md` 100% 체크.
- 전 인원 sign-off (서면 또는 슬랙 react).

---

## 9. File Map

```
apps/api/
  app/services/triage.py                                  [new]
  app/services/hospital_match.py                          [new or edit: score 계산]
  app/middlewares/disclaimer.py                           [new]
  app/api/v1/diagnose.py                                  [edit: triage + disclaimer envelope]
  app/api/v1/hospitals.py                                 [edit: specialty 필터 + score + disclaimer]
  app/config.py                                           [edit: AI_SERVER_USE_MOCK 강제 (5.7 정정 — app/core/config.py 가 아닌 app/config.py)]
  app/integrations/ai_server/mock.py                      [edit: hash 매핑 강화 (5.7 정정 — vision/audio 통합 mock 단일 파일)]
  seeds/disease_labels.json                               [reuse: W3-v2 head-start; specialty_mapping.json 의 라벨 source-of-truth]
  seeds/specialty_mapping.json                            [new — disease_labels.json 라벨 → specialty/urgency 매핑]
  seeds/demo_scenarios.py                                 [new]
  tests/test_triage.py                                    [new]
  tests/test_hospitals.py                                 [edit: specialty 케이스 (W3-v2 head-start 가 nearby PostGIS 까지 완료)]
  tests/test_disclaimer_envelope.py                       [new]
  tests/test_mock_determinism.py                          [new]
  tests/test_e2e_demo_scenarios.py                        [new]
  tests/fixtures/demo/scenario_a/{image.jpg,manifest.json} [new]
  tests/fixtures/demo/scenario_b/{audio.wav,manifest.json} [new]

apps/mobile/
  app/(tabs)/dashboard.tsx                                [new or edit]
  app/_layout.tsx                                         [edit: 의료기기 모달 1회]
  app/diagnose/result.tsx                                 [edit: "가까운 병원 →" 버튼]
  app/(tabs)/hospitals.tsx                                [edit: specialty 쿼리 자동 적용]
  src/components/dashboard/{ImageDiagnosisCard,
                            AudioDiagnosisCard,
                            DietCard,
                            BudgetPlaceholderCard}.tsx    [new]
  src/components/MedicalDisclaimer.tsx                    [reuse: W3-v2 head-start — variant prop 기반]
  src/components/DiagnosisResultCard.tsx                  [reuse: W3-v2 head-start — top-3 + action 칩 + confidence]
  src/components/HospitalListItem.tsx                     [reuse: W3-v2 head-start — tel/거리/주소]
  src/copy/medical-disclaimer-ko.ts                       [reuse: W3-v2 head-start; 금융 카피 추가 필요 (W4)]
  src/api/dashboard.ts                                    [new]

packages/shared-types/                                    [edit: triage, disclaimer, hospital score]

docs/
  w4-demo-script.md                                       [new]
  copy/disclaimers.md                                     [new]
  api/openapi-w4.json                                     [generated]
  proposal-final.pdf                                      [new or edit]

submission/
  CHECKLIST.md                                            [new, frozen Day 3 EOD]
  qa-report.md                                            [new, Day 4]
  README.md                                               [new, demo 재현 가이드]
  w4-demo-final.mp4                                       [new, Day 4]
  PetFinect-Proposal.pdf                                  [new, Day 3]
  petfinect-source.zip                                    [new, Day 4 12:00 freeze 후]
  upload-receipt.png                                      [new, Day 4 17:00]

.omc/research/
  w4-demo-cut1.mp4                                        [new, Day 2]
  w4-demo-cut2.mp4                                        [new, Day 3]
```

---

## 10. Done Definition

- [ ] AC1~AC12 중 ≥ 9개 통과 (AC10/AC11/AC12 는 반드시 통과 권장).
- [ ] mypy strict 0 errors, ruff strict 0 errors, pytest coverage ≥ 80%.
- [ ] 양 OS(iOS + Android) dev build 통과.
- [ ] `submission/` 4종 파일 모두 존재 + CHECKLIST 100% 체크.
- [ ] Day 4 17:00 KST 챌린지 포털 업로드 영수증 수령.
- [ ] 의료/금융 디스클레이머 정책 위반 0건.
- [ ] 시연 영상 결정성 검증 — Scenario A/B 라이브 시연 시 동일 결과 보장.

---

## 11. Open Questions

1. **시연 영상 보이스오버 주체** — PM 가성 녹음 vs commercial TTS(Naver Clova/Polly 등) vs 외주. Day 1 EOD 까지 PM 결정 필요. 현재 가정: PM 가성 + TTS fallback.
2. **EAS Build 인증서/keystore** — Apple Developer 계정 + Android keystore 가 W3-v2 단계까지 셋업되었는지 확인 필요. 미셋업 시 Day 2 까지 셋업 우선순위 상승. [추정: W3-v2 에서 dev build 1회는 진행했을 것]
3. **사업계획서 PDF 최종본 디자인** — 디자이너 부재 시 Keynote/Google Slides 표준 템플릿 사용. 8.28 본선 시점에 디자인 재작업 가정.
4. **GitHub 비공개 저장소 ZIP 의 의존성 lockfile 포함 여부** — `pnpm-lock.yaml`, `uv.lock` 포함 권장. `.git/` 폴더 제외(`git archive HEAD --format=zip`).
5. **specialty enum 5개로 충분한가** — 응급(emergency)·내과(internal)·피부과(dermatology)·안과(ophthalmology)·이비인후과(ENT) 만 포함. 정형/치과/소화기 라벨이 W3-v2 카탈로그에 추가되면 매핑 충돌. Day 1 라벨 catalog 확인 후 enum 확장 필요할 수 있음.
6. **Caretail 완전 제거(2026-05-07)** — 워치 통합은 본선 포함 전체 out of scope. `HealthProvider`/`HealthSnapshot` 코드 자산은 이미지/오디오 진단 저장용으로 재활용. `CARETAIL_*` 환경변수는 deprecated 주석으로 보존(follow-up).
7. **금융 디스클레이머 카피 법무 검토** — 자문 부재 → 본선 단계에서 변호사/금융감독원 가이드 재검토 필요. W4 는 PM 자체 점검 + 자문 수의사 1인.

> 본 plan 의 미결 사항은 `.omc/plans/open-questions.md` 에 누적.

---

## 12. Changelog

- 2026-05-04 — 초안 작성. 상위 SOT(`~/.claude/plans/jazzy-roaming-rose.md`) 의 W4-v2 분담을 기반으로 4일 일정 + Day 4 시간 단위 freeze 일정 + 12 AC + 7 risks + ASCII bar chart + 제출 패키지 frozen checklist 포함. 의료비/적금은 placeholder 카드로 본선 보류, 시연 영상은 멀티모달 데모로 대체.
- 2026-05-07 — **Caretail 워치 통합 완전 제거** (2026-05-07 결정). 대시보드 4섹션 → 3섹션 (이미지/오디오/식이). WatchCard 삭제. Scenario B 워치 mock 연결 제거 → 기침 음성 + 식이 처방식만. demo_scenarios.py 양 시나리오 워치 데이터 없음. Out of Scope 에 Caretail 항목 추가.
- 2026-05-07 (head-start) — W3-v2 head-start 8일 선행 결과물 반영. File Map 의 reuse 후보 명시:
  - `apps/api/seeds/disease_labels.json` (4 region × 5 + 5 audio cat) — `specialty_mapping.json` 의 라벨 source-of-truth
  - 모바일 `MedicalDisclaimer`/`DiagnosisResultCard`/`HospitalListItem`/`medical-disclaimer-ko.ts` — Day 1 신규 작성 대신 dashboard 카드에서 import 만으로 재사용
  - 경로 정정: plan v1 의 `app/core/config.py` → `app/config.py`, vision/audio 분리 mock → `app/integrations/ai_server/mock.py` 통합
  - `/v1/hospitals/nearby` PostGIS ST_DWithin 본 시작일 전 완료 → Day 1 backend 트랙은 specialty filter + score 가산만 작업
  - AI 서버 mTLS scaffold (`scripts/security/gen_dev_certs.sh` + `app/security/mtls.py` + `app/serve.py`) 완료 → Day 1 트랙에서 운영 인증서 paste 만 남음
  - 학습/평가 scaffold (`scripts/{train,eval}_{vision,audio}.py`) + 다운로드 스크립트 + 의존성 (torchvision/torchaudio/librosa) 완료 → 데이터셋 다운만 시작 가능
