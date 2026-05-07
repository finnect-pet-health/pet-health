# Spec · AI 헬스 분석 (케어테일 → 추론 → 알림)

> 케어테일 워치 데이터 폴링 → 정규화 → AI 추론 → 의료비 예측 모듈 트리거 + 푸시 알림.
> 핵심 차별화 모듈. 의료비 예측 spec(05)의 입력원.

## 1. 목표

- 케어테일 공식 API에서 활동·심박·수면·체중 데이터를 안정적으로 수집.
- **3-stage AI 파이프라인**으로 이상 신호 감지 → 질병 후보 → 권장 액션을 산출.
- 결과를 의료비 예측 모듈로 자동 전달 + 푸시 알림.
- 5.25 시점 데모: 시드 데이터로 발화하는 happy path (실시간 워치 연동 권장이지만 mock provider 대비).

## 2. 데이터 수집 파이프라인

### 2.1 폴링 워커
- Redis Queue 워커가 사용자별 5분 주기로 케어테일 API 폴링 (사용량·요금 따라 조정).
- OAuth: 사용자가 앱 안에서 케어테일 계정 연동 → refresh token 안전 저장(KMS).
- 인스턴스: 하나의 워커가 다수 사용자 분산 처리 (Celery beat or RQ scheduler).
- Rate limit: 케어테일 정책에 맞춰 백오프(429 시 jitter exponential).

### 2.2 정규화 스키마

```python
class HealthSnapshot:
    id: UUID
    pet_id: UUID
    ts: datetime                  # 데이터 시점 (UTC)
    ingest_ts: datetime           # 우리 시스템 수집 시점
    source: Enum                  # 'caretail' | 'manual' | 'mock'
    activity_min: float           # 5분 윈도 활동 분
    hr_avg: float | None          # 평균 심박 (bpm)
    hr_min: float | None
    hr_max: float | None
    sleep_state: Enum             # 'awake'|'light'|'deep'|None
    weight: float | None          # kg, 일 1회 정도
    raw_blob_ref: str | None      # S3 key (raw payload, 디버그용)
    quality: float                # 0~1 (결측·노이즈 보정)
```

### 2.3 결측·이상값 처리
- 워치 미착용/오프라인 시 `quality < 0.3` → 추론 스킵.
- 심박 outlier(40 미만, 250 초과) → 자동 마스킹.
- 1일 단위 집계 테이블 `daily_health(pet_id, date, ...)` 별도 유지(시각화·예측 입력).

## 3. AI 모델 파이프라인 (3-stage)

> **2026-05-07 최종 결정**: Caretail 워치 통합 완전 제거. AI 입력은 **카메라 이미지 + 음성** 만. 본 spec 의 3-stage 시계열 파이프라인 (워치 → anomaly → 질병 LM) 은 **deprecated** — 본선 또는 Phase 2 단계에서 별도 디바이스 정해질 때 부활 검토. 멀티모달 진단은 `.omc/plans/w3-v2-multimodal-diagnosis-hospital.md` 참조.

### Stage 1 · 시계열 이상 감지
- **모델**: Univariate/Multivariate Anomaly Detection
  - 후보: `Prophet` + STL 잔차, `IsolationForest`, `Anomaly Transformer`.
  - MVP는 lightweight rolling z-score + IsolationForest 앙상블 → 빠르게.
- **입력**: 직전 14일 daily_health (활동 분, 평균 심박, 수면 deep ratio, 체중 변화율).
- **출력**: `anomaly_score ∈ [0,1]` + 기여 feature top-3.
- **임계**: `score >= 0.7` 시 Stage 2로 전이, 아니면 일별 요약만 저장.

### Stage 2 · 질병 후보 추론
- **모델**: Pretrained 펫 의료 LM/시계열 → fine-tune
  - 후보 1: PetBERT (Hugging Face) — 텍스트 증상·차트 데이터 fine-tune.
  - 후보 2: 시계열 다중분류 Transformer (자체 구현) — 활동·심박 패턴 → 질병 클래스.
  - **MVP 권장**: 후보 1을 베이스로, 데이터를 자연어 문장으로 직렬화("활동 30%↓, 심박 평균 10%↑, 식이량 20%↓ ...") → fine-tune.
- **학습 데이터** (5.25 데모용 최소 셋):
  - Kaggle Veterinary 데이터셋 (오픈 라이선스 확인)
  - 한국수의통합DB 공개 자료
  - 합성 데이터: 수의학 교재의 증상→질환 매핑을 LLM으로 augment (5.25용 보완책)
- **출력**: `top_diseases: [{label, prob, confidence_band}]` (top-3).
- **권장 액션**: `immediate` (prob>=0.5 위중) / `schedule` (0.2~0.5) / `observe` (<0.2).

### Stage 3 · 의료비 예측 트리거
- Stage 2 결과 + `Pet.breed`, `Pet.dob` → 의료비 예측 모듈(spec 05) 호출.
- 결과를 `Diagnosis` row로 저장:
```python
class Diagnosis:
    id, pet_id, ts
    anomaly_score: float
    feature_contributions: jsonb
    top_diseases: jsonb
    action: Enum
    medical_budget_id: UUID | None
```

### 3.4 모델 서빙
- **Local AI Server** (RTX 5090):
  - FastAPI + `huggingface transformers` + `torch` + `optimum` (ONNX 변환).
  - 모델 캐시: 메모리 상주 + LRU.
- **Endpoint**:
```
POST /infer/disease
  body: { pet_id, snapshots: [HealthSnapshot...], pet_meta: {breed, age, weight, conditions[]} }
  200:  { anomaly_score, top_diseases: [...], action }
```
- **인증**: 클라우드 API ↔ 로컬 AI 서버 사이는 **mTLS** + 사전공유 키 (Cloudflare Tunnel 위에서).
- **타임아웃**: 5초, 초과 시 fallback (룰 기반 anomaly 점수만 반환).

### 3.5 Fine-tuning 워크플로우 (Phase 2 본선용)
- 야간 cron: 사용자 익명화된 라벨 데이터 → S3 → 로컬 AI 서버로 sync.
- LoRA fine-tune (24h 단위, RTX 5090).
- A/B test: 새 모델 vs 기존, 70/30 트래픽.
- 모델 버전 관리: `models/{name}/{semver}/`.

## 4. 알림

### 4.1 트리거
- `action == 'immediate'` → 즉시 푸시 + 인앱 배지 + 의료비 예측 카드 노출.
- `action == 'schedule'` → 일 1회 요약 푸시.
- `action == 'observe'` → 알림 없음, 주간 리포트에 포함.

### 4.2 채널
- FCM(Android) / APNs(iOS) via Expo Notifications.
- 메시지 예: "보리(시바) — 위장 트러블 가능성 12%. 1주 관찰을 권장해요. 자세히 보기 →"

### 4.3 Quiet hours
- 사용자 설정 가능 (기본 22:00–07:00). immediate는 무시 옵션.

## 5. API 엔드포인트 (Cloud Backend)

```
POST /v1/pets/{id}/health/sync
  body: { force?: bool }
  202:  { job_id }                  # 폴링 강제 트리거 (수동 새로고침)

GET  /v1/pets/{id}/health/snapshots?since=...
  200: [HealthSnapshot...]

GET  /v1/pets/{id}/health/daily?from&to
  200: [DailyHealth...]

GET  /v1/pets/{id}/diagnoses?limit=20
  200: [Diagnosis...]

POST /v1/pets/{id}/diagnoses/dismiss
  body: { diagnosis_id, reason? }    # 사용자 피드백 → 모델 개선
  204
```

## 6. 모바일 UX

- **홈 카드**: 최근 anomaly_score 게이지 + 최근 7일 활동/심박 sparkline.
- **알림 클릭** → 상세: top_diseases 카드 + 권장 액션 + "이 증상에 어울리는 가까운 병원" 버튼(병원 매칭 spec 04로 연결).
- **피드백**: "괜찮았어요" / "병원 갔어요" → 라벨링 데이터로 활용.

## 7. 위험 & 대응

| 위험 | 대응 |
|---|---|
| 케어테일 API 승인 지연 | `HealthProvider` 인터페이스 + `MockHealthProvider`(시드 데이터) 동시 제공 |
| 의료적 오진단 우려 | UI에 "의료 진단 아님, 수의사 상담 권장" 디스클레이머 의무 노출 |
| 학습 데이터 부족 | LLM 증강 + 룰 기반 보정 + dismiss 피드백 데이터로 점진 개선 |
| 모델 추론 지연 | 5초 타임아웃 + 룰 기반 fallback |
| RTX 5090 다운 | 클라우드에 lightweight 모델(ONNX, CPU 추론) 백업 (옵셔널 Phase 2) |

## 8. 마일스톤

| W | 산출 |
|---|---|
| W1 | 케어테일 API spike, OAuth, 첫 폴링·정규화, mock provider |
| W2 | Stage 1 anomaly 모델, daily_health 집계, 기본 알림 |
| W3 | Stage 2 fine-tuned 모델 first cut, /infer/disease 엔드포인트, 의료비 모듈 연결 |
| W4 | E2E 시연 시드 데이터, 모바일 카드/알림 통합 |

## 9. 검증

- 시드 시나리오: "보리"의 14일치 시드 데이터에서 anomaly_score 추이 → Stage 2 트리거 → 알림 발화 → 의료비 카드 노출.
- 정확도 KPI(Phase 2 이후): top-3 recall, dismiss 율.
- 의료적 안전 검토: 수의사 자문 1회 (W4).
