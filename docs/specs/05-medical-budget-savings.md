# Spec · 의료비 예측 + 자동 적금 권장 (핀테크 결합)

> AI 헬스 분석(spec 02) 결과 + 품종·나이별 통계 → 향후 12개월 예상 의료비 분포 → 적금 권장 → 외부 금융 상품 연결.
> **FIN:NECT 챌린지 핵심 차별화 포인트** (AI 헬스↔돈 결정 결합).

## 1. 목표

> **2026-05-06 스코프 피벗**: 본 spec 의 의료비 예측 + 자동 적금 결합 기능은 **MVP(5.25 제출) 단계 보류, 본선용으로 부활** 결정. W4-v2 plan 에서는 placeholder 카드만 노출 ("🔒 의료비 예측 + 적금 권장은 본선 단계 공개 예정"). 본 spec 의 모델·금융 API 결합 설계는 본선 이후 별도 plan 으로 진행.

- "이 강아지는 향후 1년에 의료비가 얼마나 들 것 같다"를 분포(p50/p90)로 제시.
- 사용자가 받아들이기 쉬운 **월 적금 금액**으로 환산 + 자동 적금 가입 제안.
- 외부 금융사·오픈뱅킹 적금 상품과 연결(시간 부족 시 정적 추천 카드 + 외부 가입 페이지).
- "건강 목표 달성 → 후원" donation 캠페인 보조 결합.

## 2. 의료비 예측 모델

### 2.1 입력 변수

| 변수 | 출처 | 설명 |
|---|---|---|
| `breed` | Pet | 품종 (e.g., Shiba) |
| `age_year` | Pet.dob | 만 나이 |
| `weight` | Pet | 최근 체중 |
| `neutered` | Pet | 중성화 여부 |
| `chronic_conditions` | Pet.conditions[] | 기저질환 |
| `recent_anomaly_score` | Diagnosis | 최근 30일 평균 |
| `top_disease_risks` | Diagnosis | top-3 disease 확률 |
| `vet_visit_history` | VetVisit | 지난 12개월 진료 횟수·평균비 |

### 2.2 통계 베이스라인

- 출처: KB펫금융보고서, 한국애완동물영양학회, 펫보험사 공시 자료.
- 품종·나이대별 연 평균 의료비 분포 (mean, p50, p90) — 12개 슬롯 (xs/sm/md/lg × puppy/adult/senior).
- 5.25 데모용으로 30~50개 셀 정적 테이블 + 출처 명시.

### 2.3 예측식 (MVP, 해석가능형)

```
base = breed_age_baseline.p_q                 # q ∈ {p50, p90}
risk_multiplier = 1 + α * recent_anomaly_score
                    + β * Σ top_disease_risks[i].prob * disease_cost_factor[i]
                    + γ * chronic_factor(conditions)
predicted_q = base * risk_multiplier
```
- 계수 α/β/γ는 W3에 시드 데이터·문헌 기반으로 grid search.
- **신뢰구간**: bootstrap (n=1000) → p50/p90 외에 90% CI 동시 산출.
- Phase 2: gradient boosting(XGBoost/LightGBM) 도입, baseline feature와 동일 입력으로 fit.

### 2.4 출력 스키마

```python
class MedicalBudget:
    id: UUID
    pet_id: UUID
    computed_at: datetime
    horizon_months: int = 12
    p50: int                  # 원
    p90: int
    ci_low: int               # 90% CI lower
    ci_high: int
    drivers: jsonb            # 상위 기여 변수 ["chronic:신장", "anomaly:0.62"]
    recommended_monthly: int  # = p90 / 12
    diagnosis_id: UUID | None # 트리거된 헬스 분석 결과
```

## 3. 적금 권장 로직

### 3.1 권장 산식
- 기본: `recommended_monthly = ceil(p90 / 12 / 1000) * 1000` (천원 단위 반올림).
- 캡: 사용자가 설정한 가용 한도(월 소득의 X%) 적용.
- 할증: `chronic_conditions`이 있으면 +20%.
- 할인: `recent_anomaly_score < 0.2` 6개월 유지 시 -10% (건강 마일리지).

### 3.2 사용자 시나리오
- 카드 타이틀: "보리의 향후 1년 예상 의료비 50만원 — 월 4.2만원 적금하면 충격 없이 대비할 수 있어요."
- 액션: ① 외부 적금 상품 확인  ② 알림 설정  ③ 나중에.

## 4. 금융 API 결합

### 4.1 옵션 비교

| 방식 | 장점 | 단점 | MVP 적합도 |
|---|---|---|---|
| A. 오픈뱅킹센터 API 직접 연동 | 표준 + 실거래 | 신청·심사 길고 사업자 필요 | ❌ (사업자 미등록 자격) |
| B. 핀테크 SDK (토스·카카오페이) | UX 매끄러움 | 사업자 + 계약 필요 | ❌ |
| C. 제휴 적금사 외부 가입 페이지(딥링크) | 즉시 구현 | 인앱 가입 불가 | ✅ (5.25) |
| D. 자체 가상 적금 PoC (mock) | 시연 자유 | 실거래 없음 | ✅ (시연용 보조) |

> **MVP 채택**: C + D 병행. C는 제휴 가능한 적금/보험사 1~2곳을 골라 외부 가입 링크. D는 시연 영상에서만 발화하는 인앱 mock 가입 흐름(실거래 없음, 디스클레이머 명시).

### 4.2 외부 가입 링크 모델

```python
class SavingsProduct:
    id: UUID
    provider_name: str        # "OO은행 펫적금"
    apr: float                # 연 이율
    min_monthly: int
    deeplink_url: str         # 카카오뱅크/토스 등
    badges: list[str]         # ['펫보험제휴', '비대면가입']
    region: str               # 'KR'
```
- `GET /v1/finance/savings?monthly={amount}` → 추천 1~3개 상품.
- 사용자가 선택 시 `deeplink_url` 오픈 + 선택 이력 저장 (제휴 트래킹).

### 4.3 PoC mock 가입 (시연용)
- `POST /v1/finance/mock-enroll { savings_id, monthly }` → 가짜 계약 ID 생성, 알림 일정 등록.
- 디스클레이머: "PoC 시연 — 실제 적금이 아닙니다".

## 5. 의료비↔적금 통합 UX 흐름

```
[헬스 분석 알림] → [상세] → [의료비 예측 카드]
                              │
                              ├─ "월 4.2만원 적금 권장" → 외부 가입 링크 / mock 가입
                              ├─ "가까운 병원 보기" → 병원 매칭 spec 04
                              └─ "후원으로 함께하기" → 보호소 후원 (donation 결합)
```

- 홈 화면에도 항상 "이번 달 권장 적금" 위젯 노출 (한 줄 설명 + 진행률).
- 적금 가입 후 14일 미발화 시 "잊지 않으셨죠?" 리마인더(옵션).

## 6. 후원(donation) 보조 결합

- 사용자의 누적 건강 마일리지(예: 산책 목표 달성, 정기검진 완료) → 1회당 1,000원 후원 매칭.
- 후원처: 농림축산식품부 동물보호관리시스템(보호소 데이터) 또는 등록 NGO.
- 결제: 5.25에는 외부 후원 페이지로 이동 (인앱 결제 불필요), 본선까지 자체 결제 모듈 검토.

## 7. API 엔드포인트

```
GET    /v1/pets/{id}/budget                  # 최신 예측
POST   /v1/pets/{id}/budget/recompute        # 강제 재계산 (admin)
GET    /v1/finance/savings?monthly=...       # 추천 적금
POST   /v1/finance/mock-enroll               # 시연 mock
GET    /v1/donations/campaigns               # 후원 캠페인 (정적/공공)
POST   /v1/donations/redirect                # 후원 클릭 트래킹 + 외부 url
```

## 8. 데이터 시드 & 마일스톤

| W | 산출 |
|---|---|
| W1 | 베이스라인 통계 테이블 시딩(품종·나이별), KB펫보고서 데이터 정리 |
| W2 | 예측식 1차, MedicalBudget 모델·CRUD |
| W3 | 헬스 분석 결과 ↔ 예측 ↔ 적금 권장 통합, 외부 가입 카드 UI |
| W4 | 시연 시나리오 안정화, 후원 결합, 디스클레이머 검토 |

## 9. 검증

- 시연 시드: 보리 시바·4세·기저없음 → p50 32만, p90 50만 → 월 4.2만 권장.
- 시연 시드: 시니어 푸들·11세·신장질환 → p50 80만, p90 130만 → 월 11만 권장.
- 단위 테스트: 동일 입력 재현성, 캡/할증/할인 적용 정확성.

## 10. 컴플라이언스·디스클레이머

- "예상 의료비는 통계·AI 추정치이며 실제와 다를 수 있습니다."
- "본 서비스는 금융상품 자문이 아니며, 가입은 해당 금융사 안내에 따릅니다."
- 광고성 노출 시 표기 의무 (전자상거래법) 사전 검토.

## 11. 위험 & 대응

| 위험 | 대응 |
|---|---|
| 베이스라인 통계 출처 불명확 | KB·통계청·학회 자료로 한정, 출처 슬라이드에 명시 |
| 실 적금 연동 불가 (사업자 미등록) | 외부 가입 링크 + mock 가입 PoC로 정렬 |
| 과도한 권장으로 사용자 부담 | 가용 한도 캡 + "나중에" 옵션 |
| 의료비 과대·과소 예측 | CI 같이 노출, 분기별 재학습 |
