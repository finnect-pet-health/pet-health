# W3-v2 Plan · 멀티모달 진단(이미지 + 오디오) + 병원 매칭

> 기간: 2026-05-15(금) ~ 2026-05-21(목), 7일 · 4–5인 팀
> 상위 plan: `~/.claude/plans/jazzy-roaming-rose.md` (스코프 피벗 SOT) / `docs/specs/02-health-analysis.md` (Stage 1 시계열은 옵셔널 강등) / `.omc/research/model-and-api-deepdive.md` (모델·데이터셋·API 검증)
> 모드: 카메라/오디오 1차 입력 멀티모달 진단으로 전면 전환. 로컬 AI 서버(RTX 5090)는 Cloudflare Tunnel 위 mTLS + HMAC. mock-first + factory swap 패턴 유지. mypy strict / ruff strict / pytest coverage ≥ 80%.

**2026-05-07 추가 결정**: Caretail 워치 옵셔널 통합 항목 모두 삭제. 워치 sparkline 카드, 시계열 옵셔널 추론 언급 제거.

---

## 1. Requirements Summary

W3-v2 종료(5.21) 시점에 **이미지 진단(피부·눈·귀·잇몸 4부위) → 오디오 진단(기침/호흡 5–10초) → 병원 매칭**의 멀티모달 진단 happy path 가 mock + 실 모델 양쪽으로 동작해야 한다. 로컬 AI 서버에 `vision.py`(MobileNetV3-Small 기반) + `audio.py`(YAMNet 기반) 추론 모듈을 띄우고, 클라우드 백엔드는 S3 presigned upload + `/v1/diagnose/image|audio` 라우터 + `DiagnosisEvent` 영구 저장 + Alembic 0005 마이그레이션을 갖춘다. 모바일은 expo-camera 정지 촬영 화면, expo-av 5–10초 녹음 화면, KakaoMap 기반 가까운 병원 3곳 지도 화면을 출시한다. 병원 데이터는 LOCALDATA 폐쇄(2026-04-16) 반영해 data.go.kr 통합 인허가 OpenAPI 로 ETL 1줄 수정 + 좌표 결측 시 카카오 로컬 API 지오코딩 fallback. 모든 진단 카드에는 의료적 디스클레이머 의무 노출. 핀테크(의료비/적금)·시계열 LM(Stage 2)·통합 대시보드는 W4 또는 본선으로 이월.

### 1.1 In Scope

- **AI/인프라 (Track A)**
  - `apps/ai-server/app/inference/vision.py` — MobileNetV3-Small ImageNet pretrained → Kaggle dog skin diseases fine-tune. 4부위(피부/눈/귀/잇몸) top-3 라벨 + confidence + 권장 액션 enum(`immediate`/`schedule`/`observe`).
  - `apps/ai-server/app/inference/audio.py` — **AnimalCLAP audio encoder (HTS-AT base, MIT) frozen + custom MLP head** (512→128→5). 512-dim L2-normalized 동물 vocalization 임베딩 → 5 카테고리(`정상`/`기침`/`이상호흡`/`꼬르륵`/`기타`) + 이상 점수 ∈ [0,1]. **2026-05-07 spike 검증 완료** (`scripts/spike_animalclap.py`: `[1, 512]` 임베딩, 154M params, 590MB ckpt, CPU 7.4s/5초 클립). 실패 시 YAMNet 으로 swap 유지.
  - Fallback: ConvNeXt-Tiny via timm `convnext_tiny.fb_in1k` (이미지) / **YAMNet + MLP head** (오디오, Apache-2.0) → PANN AudioSet — 정확도 < 70% 또는 OOM 시 `AudioInferenceProvider(Protocol)` 안에서 1줄 swap.
  - `apps/ai-server/app/api/v1/{vision,audio}.py` — `POST /infer/vision`, `POST /infer/audio` (multipart + pet_meta JSON, 5초 timeout, 룰 기반 fallback).
  - mTLS + `AI_SERVER_SHARED_SECRET` HMAC 인증.
  - 데이터셋 prep: Kaggle dog skin diseases ~3k 샘플(증강 포함), Kaggle dog cough + ESC-50 dog 라벨 + 자체 합성 ~2k 샘플.
  - `apps/api/seeds/disease_labels.json` — 영어 모델 라벨 ↔ 한국어 UI 매핑 테이블.

- **백엔드 (Track B)**
  - `apps/api/app/integrations/storage/s3.py` — `boto3` 또는 `aiobotocore` 기반 presigned upload URL 발급 + multipart + content-type 검증. Mock factory(LocalStack 또는 in-memory).
  - 환경변수: `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. 미설정 시 mock 자동 폴백.
  - `apps/api/app/api/v1/diagnose.py` — `POST /v1/diagnose/image`, `POST /v1/diagnose/audio`, `GET /v1/pets/{id}/diagnoses?limit=20`.
  - 모델: `DiagnosisEvent(id, pet_id, modality enum('image','audio','timeseries'), s3_ref, top_results jsonb, action enum, confidence_top1 float, created_at)`. (HealthSnapshot 컬럼 추가는 5.7 정정 — W2 에 ORM 으로 존재하지 않아 사양에서 제외; 진단 데이터는 DiagnosisEvent 단일 테이블에 저장.)
  - Alembic `0005_multimodal_diagnosis` 마이그레이션.
  - 병원 매칭 업그레이드: `infra/etl/hospital_sync.py` 1줄 수정으로 data.go.kr 통합 인허가 OpenAPI 채택 + 카카오 로컬 API 지오코딩 fallback. `Hospital` PostGIS POINT 컬럼 + `ST_DWithin`. `GET /v1/hospitals/nearby?lat=&lng=&radius_m=&limit=&specialty=` (specialty 옵셔널).

- **모바일 (Track C)**
  - `apps/mobile/app/diagnose/camera.tsx` — expo-camera 정지 촬영 + 4부위 선택 모달 + S3 presigned 업로드 + 결과 카드 + 디스클레이머.
  - `apps/mobile/app/diagnose/audio.tsx` — expo-av 5–10초 녹음 + 카운트다운 UI + S3 업로드 + 결과 카드.
  - `apps/mobile/app/hospitals/index.tsx` — KakaoMap WebView(W1 spike 컴포넌트 재사용) + 가까운 3개 동물병원 마커 + 마커 탭 시 상세(전화/주소/진료시간).
  - `apps/mobile/src/api/diagnose.ts` — `uploadAndDiagnose(modality, fileUri)` 단일 함수.

- **리드/PM (Track D)**
  - 데이터셋 라이선스 검수 + 다운로드 스크립트(`scripts/datasets/{skin,audio}_download.sh`).
  - 한국어 라벨 매핑 테이블 큐레이션 + 수의사 자문 1회 권장.
  - 의료적 디스클레이머 카피 검수(모든 진단 카드 의무).
  - W4-v2 카드 분해 초안.
  - mypy strict / ruff strict / coverage ≥ 80% 가드.
  - shared-types codegen 확장(diagnosis, hospital nearby).

### 1.2 Out of Scope (W4-v2 또는 본선)

- 진단 결과 → 진료과(specialty) 매칭 알고리즘(triage service) — **W4-v2 Track A**.
- 통합 건강 대시보드 화면(이미지·오디오·식이 3섹션) — **W4-v2 Track B**.
- 의료비 placeholder 카드 — **W4-v2 Track B**(본선 부활).
- 90초 시연 영상 — **W4-v2 Track D**.
- Stage 2 시계열 LM — **Phase 2 / 본선**.
- 적금 권장 카드, 외부 가입 딥링크, 후원 결합 — **본선**.
- 실 결제·오픈뱅킹 직접 연동 — Out.
- Caretail 워치 통합 일체 (옵셔널·mock 포함). HealthProvider 코드 자산은 이미지/오디오 진단 데이터 저장용으로 재활용 (image_s3_ref/audio_s3_ref/inference_metadata 컬럼).

### 1.3 Constraints

- 2026-05-07 결정: Caretail 워치 통합 완전 제거. `HealthProvider`/`MockHealthProvider`/`HealthSnapshot` 은 W2 에서 Pydantic 메모리 스키마로만 존재 (DB ORM 모델 아님) — `CARETAIL_*` 환경변수 및 폴링 워커는 삭제 대상. 진단 데이터 저장은 DiagnosisEvent 단일 테이블 (s3_ref + top_results jsonb) 로 일원화. (5.7 정정: 기존 plan v2 의 "HealthSnapshot 컬럼 재활용" 가정은 ORM 부재로 무효.)
- 4–5인 팀 분담(백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1). 5.17 일요일은 작업 가능, 5.20 수요일은 mypy/ruff/coverage 회복 데이로 신규 코드 지양.
- **Day 7(5.21)** 은 freeze + 통합 + W4-v2 카드 분해 + 시연 시드 데이터 준비 전용. 신규 코드 금지.
- 모든 진단 카드(이미지/오디오 결과)에 "AI 추정치, 수의사 상담 권장" 디스클레이머 의무 노출(spec 02 § 7, spec 05 § 10).
- 로컬 AI 서버(RTX 5090) 는 Cloudflare Tunnel 위 mTLS + `AI_SERVER_SHARED_SECRET` HMAC 의무.
- 외부 통합은 W1·W2 동일하게 Provider 추상 + factory swap-ready 패턴 유지(이미지·오디오·storage·hospital).
- 데이터셋 라이선스 미확정 시 자체 합성/증강 데이터로 대체(R1).

---

## 2. Acceptance Criteria (testable)

| # | 기준 | 검증 방법 |
|---|---|---|
| AC1 | `alembic upgrade head` 실행 시 `diagnosis_event` 테이블 + `hospital.location`(PostGIS POINT) 컬럼 반영 | `psql -c "\d diagnosis_event"` `\d hospital` 출력 검증 (5.7 정정: health_snapshot 컬럼 요구 제거 — W2 ORM 부재) |
| AC2 | `apps/ai-server` 컨테이너 부팅 후 `POST /infer/vision` (mock 모델) 에 224×224 RGB JPEG + `pet_meta` JSON 전송 시 200 + `{top_results: [...3건], action: 'observe'|'schedule'|'immediate', confidence_top1}` 반환, 5초 timeout 내 | `pytest apps/ai-server/tests/test_vision_infer.py::test_vision_smoke_mock` |
| AC3 | MobileNetV3-Small 의 Kaggle dog skin diseases holdout(20% split) top-1 정확도 ≥ 70% **또는** ConvNeXt-Tiny fallback 으로 ≥ 70% 도달 (둘 중 하나 채택 결정 기록) | `apps/ai-server/scripts/eval_vision.py` 결과 표 + `docs/ai/vision-eval-w3.md` 첨부 |
| AC4 | `POST /infer/audio` (mock) 에 5–10초 16kHz mono WAV/M4A + `pet_meta` 전송 시 200 + `{score: float ∈ [0,1], category: '정상'|'기침'|'이상호흡'|'꼬르륵'|'기타'}` 반환 | `pytest apps/ai-server/tests/test_audio_infer.py::test_audio_smoke_mock` |
| AC5 | **AnimalCLAP encoder + MLP head** holdout 에서 binary "기침 vs 비기침" F1 ≥ 0.75. 미달 시 YAMNet fallback 으로 1줄 swap 후 동일 임계 재시도. 채택 모델 + 평가 표 기록 의무 | `apps/ai-server/scripts/eval_audio.py` 결과 표 + `docs/ai/audio-eval-w3.md` |
| AC6 | 클라우드 → 로컬 AI 서버 호출 시 mTLS handshake 성공 + `X-AI-HMAC` 헤더 누락 시 401, 잘못된 HMAC 시 403 | `pytest apps/ai-server/tests/test_auth.py::test_mtls_and_hmac` (httpx + 자체 서명 인증서 fixture) |
| AC7 | `POST /v1/diagnose/image` body `{pet_id, image_s3_key}` → S3 객체 GET → 로컬 AI `/infer/vision` 호출 → `DiagnosisEvent(modality='image')` 1 row 적재 + 응답에 `top_results` 포함 | `pytest apps/api/tests/test_diagnose.py::test_image_diagnose_happy_path` (mock S3 + mock AI server) |
| AC8 | `POST /v1/diagnose/audio` body `{pet_id, audio_s3_key}` → 동일 흐름 + `DiagnosisEvent(modality='audio')` 적재 | `pytest ::test_audio_diagnose_happy_path` |
| AC9 | `GET /v1/pets/{id}/diagnoses?limit=20` 가 최신 20건 created_at desc 정렬 반환 + 가족 멤버 RBAC(다른 가족 펫 접근 시 404) | `pytest ::test_diagnoses_list_rbac` |
| AC10 | S3 presigned upload URL 발급 (`POST /v1/uploads/presign?modality=image`) → 응답 URL 로 PUT 시 200 + 잘못된 content-type 거부(`application/octet-stream` 등) | `pytest apps/api/tests/test_uploads.py::test_presign_and_put` (LocalStack 또는 in-memory mock) |
| AC11 | `infra/etl/hospital_sync.py` 가 data.go.kr 통합 인허가 OpenAPI(또는 mock 50건 시드)로 50개+ 동물병원 row 적재 + 좌표 결측 row 는 카카오 로컬 API 지오코딩으로 보정(또는 mock fallback) | `pytest infra/etl/tests/test_hospital_sync.py::test_etl_with_geocode_fallback` + `psql -c "SELECT count(*) FROM hospital WHERE location IS NOT NULL"` ≥ 50 |
| AC12 | `GET /v1/hospitals/nearby?lat=37.5&lng=127.04&radius_m=3000&limit=3` 가 PostGIS `ST_DWithin` 으로 3건 이하 반환 + 거리 오름차순 정렬 + `specialty=` 쿼리 파라미터 (옵셔널, W4 triage 에서 활용 예정) 무시되더라도 200 | `pytest apps/api/tests/test_hospitals.py::test_nearby_postgis` |
| AC13 | 모바일 카메라 화면: 4부위 선택 모달 → expo-camera 촬영 → S3 presigned 업로드 → 진단 결과 카드(라벨 top-3 + 권장 액션 + 의료적 디스클레이머) 표시. 시연 영상 30초 | `.omc/research/w3-camera-demo.mp4` + `docs/w3-camera-demo.md` |
| AC14 | 모바일 오디오 화면: 5–10초 카운트다운 → expo-av 녹음 → S3 업로드 → 진단 결과 카드(이상 점수 + 카테고리 + 디스클레이머). 시연 영상 30초 | `.omc/research/w3-audio-demo.mp4` |
| AC15 | 모바일 병원 화면: KakaoMap WebView 위 가까운 3개 마커 + 마커 탭 시 상세(전화/주소/진료시간) 노출 + W1 spike 컴포넌트 재사용 확인 | `.omc/research/w3-hospital-demo.mp4` + `apps/mobile/src/components/KakaoMapView.tsx` import 라인 grep |
| AC16 | `mypy app` 0 errors, `ruff check .` 0 errors, `pytest --cov=app --cov-fail-under=80` 통과 (apps/api + apps/ai-server 양쪽) + shared-types codegen 후 `pnpm -C apps/mobile typecheck` 0 errors | CI 로그 (`.github/workflows/{api,ai-server,mobile}.yml`) green |

> Done 임계: 16개 중 ≥ 12개 통과(목표 13~14). 미통과는 W4-v2 첫날 보강 카드.

---

## 3. Implementation Steps (Day 단위)

### 3.1 Day 1 (5.15 금) — 데이터셋 라이선스 + 다운로드 + 스토리지/Alembic

> W2-v2 freeze 해제. mock-first 유지하되 이미지·오디오 데이터셋 다운로드를 가장 먼저 시작(R1 데이터셋 가용성).

#### 트랙 A · 데이터셋 다운로드 + 라벨 스키마 (AI/infra)
- [ ] `scripts/datasets/skin_download.sh` — Kaggle CLI 로 "Dog's skin diseases (Image Dataset)" 다운로드 + train/val 8:2 split + `apps/ai-server/data/skin/` 적재.
- [ ] `scripts/datasets/audio_download.sh` — Kaggle dog cough + ESC-50 dog 라벨 추출 + `apps/ai-server/data/audio/` 적재.
- [ ] `apps/api/seeds/disease_labels.json` 초안 — 영어 모델 라벨 ↔ 한국어 UI(피부/눈/귀/잇몸 4부위 × 의심 라벨 ~5종).
- [ ] 라이선스 노트 `docs/data/dataset-licenses-w3.md` (Kaggle 라이선스 + ESC-50 BSD-3 + 자체 augmentation 출처).

#### 트랙 B · S3 storage + Alembic 0005 (backend lead)
- [ ] `apps/api/app/integrations/storage/__init__.py`:
  ```python
  class StorageProvider(Protocol):
      async def presign_put(self, key: str, content_type: str, ttl_s: int = 600) -> str: ...
      async def presign_get(self, key: str, ttl_s: int = 600) -> str: ...
      async def fetch_bytes(self, key: str) -> bytes: ...
  ```
- [ ] `apps/api/app/integrations/storage/s3.py` — `aiobotocore` 기반 real provider. `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` 부재 시 `RuntimeWarning` + factory mock 자동 강등.
- [ ] `apps/api/app/integrations/storage/{mock,factory}.py` — in-memory mock(테스트용) + LocalStack 옵션. content-type 화이트리스트(`image/jpeg`, `image/png`, `audio/wav`, `audio/m4a`, `audio/mpeg`).
- [ ] `apps/api/app/api/v1/uploads.py` 신규 — `POST /v1/uploads/presign?modality=image|audio` (AC10).
- [ ] `apps/api/app/models/diagnosis_event.py` 신규: `DiagnosisEvent(id, pet_id FK, modality enum('image','audio','timeseries'), s3_ref, top_results jsonb, action enum('immediate','schedule','observe'), confidence_top1 float, created_at)`.
- [ ] `apps/api/app/models/hospital.py` 에 `location: Geometry('POINT', srid=4326)` 컬럼 추가(geoalchemy2).
- [ ] `alembic revision --autogenerate -m "0005_multimodal_diagnosis"` → 검증 → commit (AC1).
- [ ] `apps/api/tests/test_uploads.py` — AC10 (LocalStack 또는 in-memory mock fixture).

#### 트랙 C · 모바일 expo-camera/expo-av 셋업 (mobile dev)
- [ ] `pnpm -C apps/mobile add expo-camera expo-av expo-file-system` (이미 있다면 버전 확인).
- [ ] `apps/mobile/app/diagnose/_layout.tsx` 신규 — diagnose 스택 네비게이션.
- [ ] expo-camera 권한 요청 헬퍼 `apps/mobile/src/permissions/camera.ts` + expo-av 권한 헬퍼 `apps/mobile/src/permissions/audio.ts`.
- [ ] EAS Build dev client 1회 빌드(W2-v2 푸시 토큰 빌드와 합쳐 진행 가능, 실패 시 시연은 expo-go 한정).

#### 트랙 D · 라이선스 + 디스클레이머 카피 (lead/PM)
- [ ] `docs/copy/medical-disclaimer-ko.md` 작성 — 진단 카드 푸터 카피 3줄(이미지/오디오/병원).
- [ ] 데이터셋 라이선스 표 1차 검수(트랙 A 와 협업).
- [ ] W3-v2 Kanban 카드 16개(AC1~AC16) 분배 + 일정 표.

**Day 1 종료 조건**: AC1, AC10 통과. 데이터셋 다운로드 완료(이미지 ≥ 2k, 오디오 ≥ 1k 확보) + 라벨 스키마 v0.

---

### 3.2 Day 2 (5.16 토) — Vision/Audio 추론 모듈 + 로컬 AI 서버 mTLS

> AI/infra 트랙 메인 데이. fine-tune 학습 잡은 백그라운드(GPU)로 굴리며 코드를 채운다.

#### 트랙 A · `apps/ai-server` Vision/Audio 모듈 (AI/infra)
- [ ] `apps/ai-server/app/inference/vision.py`:
  ```python
  class VisionInference(Protocol):
      async def predict(self, img_bytes: bytes, pet_meta: PetMeta) -> VisionResult: ...
  ```
  - `MobileNetV3SmallVision` 실 구현 — torchvision pretrained → 4부위 head fine-tune. 224×224 RGB resize + ImageNet normalize.
  - `MockVision` — 결정적 dummy 결과(시연·테스트용).
  - `ConvNeXtTinyVision` fallback — 정확도 < 70% 시 1줄 swap.
- [ ] `apps/ai-server/app/inference/audio.py`:
  - `AnimalCLAPAudio` 실 구현 (1차) — `risashinoda/animalclap` HF 다운로드 → audio encoder frozen → **512-dim L2-normalized 임베딩** → MLP head(512→128→5 카테고리). 참조: `scripts/spike_animalclap.py` (이미 검증 통과). API 함정: `ClapProcessor(audio=...)` 키워드, `get_audio_features()` 는 `BaseModelOutputWithPooling` 반환 → `.pooler_output` 사용. GPU sm_75+ 필요 (GTX 1060 비호환 — CPU fallback 권장).
  - `YAMNetAudio` fallback 구현 (2차) — YAMNet TF/HF port → embeddings → MLP head(64→32→5 카테고리). `AudioInferenceProvider(Protocol)` 추상 안에서 swap.
  - 입력: 5–10s wav/m4a → 16kHz mono resample → 0.96s frame stack.
  - `MockAudio` — 결정적 score + category.
  - `PANNAudio` fallback.
- [ ] `apps/ai-server/app/schemas/{vision,audio}.py` Pydantic IO 스키마.
- [ ] `apps/ai-server/tests/test_vision_infer.py` — AC2 (mock smoke).
- [ ] `apps/ai-server/tests/test_audio_infer.py` — AC4 (mock smoke).

#### 트랙 B · 로컬 AI 서버 라우터 + mTLS + HMAC (AI/infra + backend lead)
- [ ] `apps/ai-server/app/api/v1/vision.py` — `POST /infer/vision` (multipart `file` + `pet_meta` JSON form field). 5s timeout, 룰 기반 fallback(이미지 hash → "관찰 권장" 기본).
- [ ] `apps/ai-server/app/api/v1/audio.py` — `POST /infer/audio` (multipart `file` + `pet_meta`). 5s timeout, 룰 기반 fallback.
- [ ] `apps/ai-server/app/security/hmac_auth.py` — `X-AI-HMAC` 헤더 검증 (요청 본문 SHA-256 + `AI_SERVER_SHARED_SECRET`). 누락 401, 불일치 403.
- [ ] `apps/ai-server/app/security/mtls.py` — Cloudflare Tunnel + mTLS 인증서 검증(uvicorn `ssl_certfile`/`ssl_keyfile`/`ssl_ca_certs`).
- [ ] 인증서 발급 스크립트 `scripts/security/gen_dev_certs.sh` (자체 서명, dev only).
- [ ] `apps/ai-server/tests/test_auth.py` — AC6 (mTLS handshake fixture + HMAC 케이스).

#### 트랙 C · 데이터셋 fine-tune 학습 잡 (AI/infra, GPU 백그라운드)
- [ ] `apps/ai-server/scripts/train_vision.py` — MobileNetV3-Small head replace + 1~3 epoch fine-tune, augmentation(albumentations: flip/rotate/colorjitter) 으로 ~3k 샘플 도달.
- [ ] `apps/ai-server/scripts/train_audio.py` — **AnimalCLAP encoder embeddings 추출** (frozen) → MLP head LoRA 1 epoch (50–100 자체 녹음 + Kaggle 개 기침). YAMNet 대체 경로도 동일 스크립트로 `--encoder yamnet` 플래그.
- [ ] **GPU 작업은 `run_in_background` 로 굴리고 Day 3 평가에서 결과 회수**.

#### 트랙 D · shared-types codegen 확장 (lead/PM)
- [ ] `packages/shared-types/openapi.ts` 재생성 — diagnosis(image/audio), upload presign, hospital nearby 스키마 포함.
- [ ] `apps/mobile/src/api/types.ts` 가 shared-types import.

**Day 2 종료 조건**: AC2, AC4, AC6 통과(mock 경로). fine-tune 학습 잡 결과 회수 직전.

---

### 3.3 Day 3 (5.17 일) — Diagnose 라우터 + DiagnosisEvent + 모델 평가

#### 트랙 A · `/v1/diagnose/*` 라우터 (backend lead)
- [ ] `apps/api/app/api/v1/diagnose.py` 신규:
  - `POST /v1/diagnose/image` body `{pet_id, image_s3_key}` → 스토리지 fetch → 로컬 AI `/infer/vision` POST(mTLS+HMAC) → `DiagnosisEvent(modality='image')` 적재 → 응답.
  - `POST /v1/diagnose/audio` body `{pet_id, audio_s3_key}` → 동일 흐름 → `DiagnosisEvent(modality='audio')` 적재 → 응답.
  - `GET /v1/pets/{id}/diagnoses?limit=20` — created_at desc, RBAC(가족 멤버만).
- [ ] `apps/api/app/services/diagnose.py` — 호출 흐름 추상화 + 5초 timeout + 룰 기반 fallback(상위 라우터 200 유지).
- [ ] `apps/api/app/integrations/ai_server/{__init__,real,mock,factory}.py` — `AIServerClient` Protocol + httpx 실 구현(mTLS + HMAC) + mock(결정적).
- [ ] `apps/api/tests/test_diagnose.py` — AC7, AC8, AC9 (mock S3 + mock AI server fixture).

#### 트랙 B · 모델 평가 + 채택 결정 (AI/infra)
- [ ] `apps/ai-server/scripts/eval_vision.py` — holdout 20% top-1 정확도 측정. < 70% 시 ConvNeXt-Tiny fallback 학습 시도.
- [ ] `apps/ai-server/scripts/eval_audio.py` — holdout F1 (기침 vs 비기침 binary + 5-class macro-F1).
- [ ] 평가 결과 표 → `docs/ai/vision-eval-w3.md`, `docs/ai/audio-eval-w3.md` (AC3, AC5).
- [ ] 채택 모델 결정 commit + factory 기본값 갱신.

#### 트랙 C · 모바일 카메라 화면 v0 (mobile dev)
- [ ] `apps/mobile/app/diagnose/camera.tsx` 화면 골격:
  - 4부위 선택 모달(피부/눈/귀/잇몸).
  - expo-camera 정지 촬영 → 임시 파일.
  - presign 호출 → S3 PUT → `POST /v1/diagnose/image`.
  - 결과 카드(top-3 라벨 + confidence 바 + 권장 액션 칩 + 의료적 디스클레이머 푸터).
- [ ] `apps/mobile/src/api/diagnose.ts` — `uploadAndDiagnose(modality, fileUri)` 단일 함수.

#### 트랙 D · 한국어 라벨 매핑 큐레이션 (lead/PM)
- [ ] `apps/api/seeds/disease_labels.json` v1 — 4부위 × 의심 라벨 한국어 카피 확정.
- [ ] 수의사 자문 1회 약속 잡기(W4-v2 Day 1~2 까지 review, R5 대비).

**Day 3 종료 조건**: AC3, AC5, AC7, AC8, AC9 통과(mock + 실 모델 양쪽). 모바일 카메라 화면이 시연 가능한 수준.

---

### 3.4 Day 4 (5.18 월) — 모바일 오디오 화면 + 병원 ETL 업그레이드

#### 트랙 A · 모바일 오디오 화면 (mobile dev)
- [ ] `apps/mobile/app/diagnose/audio.tsx`:
  - 카운트다운 UI(3-2-1 → 녹음 시작) + 5–10초 시각 게이지.
  - expo-av `Audio.Recording` → m4a 출력 → presign PUT → `POST /v1/diagnose/audio`.
  - 결과 카드(이상 점수 게이지 + 카테고리 칩 + 디스클레이머).
- [ ] `apps/mobile/src/components/RecordingIndicator.tsx` (시각 게이지).
- [ ] `apps/mobile/src/components/DiagnosisResultCard.tsx` (image/audio 공용).

#### 트랙 B · Hospital ETL + Nearby 라우터 (backend lead + AI/infra)
- [ ] `infra/etl/hospital_sync.py` 1줄 수정:
  - LOCALDATA(폐쇄) → data.go.kr 통합 인허가 OpenAPI(`tn_pubr_public_animal_hospital_info_api` 또는 사용자 활용신청 후 endpoint URL).
  - **Decoding 키**를 `params=` 딕셔너리에 넣는 경로(.omc/research § 4.4).
  - 좌표 결측 row → 카카오 로컬 API 지오코딩 (`KAKAO_REST_API_KEY` + `https://dapi.kakao.com/v2/local/search/address.json`).
  - 폴백: `apps/api/seeds/hospitals_seoul.json` 50건 정적 시드.
- [ ] `apps/api/app/api/v1/hospitals.py`:
  - `GET /v1/hospitals/nearby?lat=&lng=&radius_m=&limit=&specialty=` — PostGIS `ST_DWithin(location, ST_MakePoint(lng, lat)::geography, radius_m)` + 거리 ASC.
  - `specialty` 쿼리는 W3-v2 에서는 무시(파라미터만 수용, W4-v2 triage 에서 활용).
- [ ] `apps/api/tests/test_hospitals.py` — AC11, AC12.
- [ ] `infra/etl/tests/test_hospital_sync.py` — AC11(geocode fallback 케이스).

#### 트랙 C · 병원 모바일 화면 (mobile dev)
- [ ] `apps/mobile/app/hospitals/index.tsx`:
  - W1 spike `KakaoMapView` WebView 컴포넌트 재사용.
  - 사용자 현재 위치(expo-location, 권한 요청 1회) → `/v1/hospitals/nearby?limit=3`.
  - 마커 3개 + 탭 시 상세 sheet(전화 `tel:` 링크, 주소, 진료시간).
- [ ] `apps/mobile/src/api/hospitals.ts`.

#### 트랙 D · 디스클레이머 + 카피 검수 (lead/PM)
- [ ] 모든 결과 카드에 디스클레이머 노출 검수(카메라/오디오/병원).
- [ ] 의료적 디스클레이머 카피 확정 → `docs/copy/medical-disclaimer-ko.md` v1.

**Day 4 종료 조건**: AC11, AC12, AC14 통과. 모바일 3개 화면 모두 시연 가능 수준.

---

### 3.5 Day 5 (5.19 화) — E2E 통합 + 시연 시드 데이터 + 룰 기반 fallback 점검

#### 트랙 A · E2E 통합 테스트 (backend lead + mobile dev)
- [ ] `apps/api/tests/test_e2e_diagnose.py` — presign → S3 PUT → diagnose → 응답 + DB row 확인 (실 S3 또는 LocalStack).
- [ ] `apps/mobile/e2e/diagnose.spec.ts` — Detox/Maestro 카메라 → 결과 카드 1 회.
- [ ] 시연용 결정성 보장: `AI_SERVER_USE_MOCK=1` + `disease_labels.json` 고정.

#### 트랙 B · 룰 기반 fallback (AI/infra)
- [ ] 5초 timeout 또는 모델 OOM 시 룰 기반 응답 경로 검증:
  - 이미지: 빨간 픽셀 비율 → "피부 염증 의심 확인 필요" 1건 + action='observe'.
  - 오디오: RMS energy + zero-crossing rate → 0.3~0.7 score, category='기타' 기본.
- [ ] `apps/ai-server/app/inference/fallback.py` 모듈화.

#### 트랙 C · 시연 시드 데이터 큐레이션 (AI/infra + lead/PM)
- [ ] `apps/ai-server/data/demo/{skin_redness.jpg, eye_discharge.jpg, ear_inflam.jpg, gum_paleness.jpg, cough_5s.wav, breath_irreg_8s.wav}` 6건 시연 셋.
- [ ] 시드 결과 결정성 확인(mock provider 강제 시 동일 결과 반복).

#### 트랙 D · 진단 결과 카드 UX 다듬기 (mobile dev)
- [ ] 권장 액션별 색상 토큰(immediate=red, schedule=amber, observe=blue).
- [ ] confidence 바 시각화.
- [ ] 디스클레이머 푸터 고정.
- [ ] 모바일 다크모드 호환 점검.

**Day 5 종료 조건**: AC13, AC14, AC15 시연 영상 1차 촬영 가능.

---

### 3.6 Day 6 (5.20 수) — mypy/ruff/coverage 회복 + shared-types 적용 + W4-v2 카드 분해

> **신규 기능 코드 동결**. 타입·문서·테스트·차주 카드.

- [ ] `mypy app` 0 errors 회복(apps/api + apps/ai-server)(AC16).
  - W3-v2 진행 중 누적된 `# type: ignore` 제거.
  - geoalchemy2 / aiobotocore stubs 추가 (mypy.ini `[mypy-geoalchemy2.*] ignore_missing_imports = True` 한정 완화).
- [ ] `ruff check . --fix` 후 잔여 violation 수동 정리.
- [ ] `pytest --cov=app --cov-fail-under=80` 통과 확인. 부족 시 happy-path 테스트 보강.
- [ ] `packages/shared-types` codegen 실행 + mobile typecheck 통과(AC16).
- [ ] `.omc/plans/w4-v2-triage-dashboard-demo.md` 초안 — 진단 결과 → 진료과 매칭(triage) + 통합 대시보드 + 의료비 placeholder + 시연 영상 + 90초 컷 시트를 4일 일정(5.22~5.25)으로 분배.
- [ ] `.omc/plans/open-questions.md` 갱신 — W3-v2 발견 미결 질문 5–8개 누적.

---

### 3.7 Day 7 (5.21 목) — Freeze · 통합 · 시연 시드 · W4-v2 카드 finalize

- [ ] AC1~AC16 점검표 갱신, 통과 ≥ 12 확인(목표 13~14).
- [ ] `docs/w3-v2-retrospective.md` — 잘 된 것/막힌 것/W4-v2 이월.
- [ ] OpenAPI export → `docs/api/openapi-w3-v2.json`.
- [ ] 통합 시연 영상 1차(카메라 → 오디오 → 병원 90초) → `.omc/research/w3-v2-demo.mp4`.
- [ ] `.omc/research/api-applications/` 데이터셋 라이선스 + data.go.kr 키 발급 상태 스냅샷.
- [ ] W4-v2 카드 분해 finalize(`.omc/plans/w4-v2-triage-dashboard-demo.md`).
- [ ] 신규 코드 금지. 모바일 시연 영상 갱신 + 디스클레이머 최종 검수만.

---

## 4. Risks & Mitigations

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | Kaggle "Dog's skin diseases" 데이터셋 라이선스 또는 다운로드 실패(계정 인증·로봇 차단·비공개 전환) | 中 | 高 | Day 1 최우선 다운로드. 실패 시 Roboflow Open Images "dog" + 자체 스마트폰 촬영 100장 augmentation 으로 대체. AC3 임계 70% 미달 시 ConvNeXt-Tiny + augmentation 강화로 1회 재시도, 그래도 미달 시 mock 경로로 AC2/AC7 만 통과시키고 AC3 는 W4-v2 첫날 보강. |
| R2 | MobileNetV3-Small fine-tune 정확도 < 70% (데이터 부족·라벨 노이즈) | 中 | 中 | ConvNeXt-Tiny fallback 1줄 swap. augmentation(flip/rotate/colorjitter/cutout) 강화. 그래도 미달 시 평가 결과 정직하게 기록 + 시연은 결정적 mock + 룰 기반 fallback. |
| R3 | YAMNet TF/HF port 호환성 또는 16kHz mono resample 실패 | 中 | 中 | TF Hub `yamnet` 직접 로드 우선, 실패 시 `torchaudio` + PANN AudioSet pretrained 1줄 swap. resample 은 `librosa.resample` 표준 경로. |
| R4 | 로컬 AI 서버 mTLS 인증서 발급/갱신 실패 또는 Cloudflare Tunnel 다운 | 中 | 高 | 자체 서명 인증서 dev 경로 + `AI_SERVER_SHARED_SECRET` HMAC 단일 인증으로 일시 강등 가능(`AI_SERVER_REQUIRE_MTLS=false`). 시연 직전 회복 의무. CI 는 자체 서명 fixture 사용. |
| R5 | 한국어 라벨 매핑 수의사 자문 미확보(시간 부족) | 中 | 中 | W3-v2 안에서는 lead/PM 가 1차 큐레이션, W4-v2 Day 1~2 내 자문 1회 의무. 미확보 시 디스클레이머 가중 노출(`docs/copy/medical-disclaimer-ko.md` v2). |
| R6 | data.go.kr 통합 인허가 OpenAPI 활용신청 승인 지연 | 中 | 中 | LOCALDATA 폐쇄 반영. 정적 50건 시드(`apps/api/seeds/hospitals_seoul.json`)로 AC11/AC12 통과. 본선 전 swap. **Decoding 키** params 경로 통일. |
| R7 | S3 보안 (presigned URL 노출, content-type spoofing, anonymous PUT) | 低 | 高 | content-type 화이트리스트, presigned URL TTL 10분, bucket policy 로 anonymous PUT 차단, Origin/Referer 검증. CI 에 anonymous PUT 거부 테스트. |
| R8 | RTX 5090 다운/과열 또는 GPU 메모리 부족 | 低 | 高 | 클라우드 백엔드는 5초 timeout + 룰 기반 fallback 으로 200 유지. ONNX 변환 + CPU fallback 옵션 W4-v2 또는 Phase 2. mock provider 강제(`AI_SERVER_USE_MOCK=1`) 1줄 swap 가능. |
| R9 | expo-camera/expo-av 권한 거부 또는 expo-go 환경 제한 | 中 | 中 | Day 1 EAS Build dev client 1회 빌드(W2-v2 푸시와 합쳐). 권한 거부 시 시연은 갤러리 업로드 fallback(`expo-image-picker`). |
| R10 | KakaoMap WebView 렌더 실패(W1 spike 컴포넌트 재사용 깨짐) | 低 | 中 | W1 spike `KakaoMapView.tsx` 회귀 테스트 1회. 실패 시 react-native-maps + OpenStreetMap fallback 짧은 경로. |
| R11 | `mypy strict` 회복이 Day 6 하루로 부족(geoalchemy2/aiobotocore stubs) | 中 | 中 | Day 1~5 동안 새 코드는 처음부터 strict 통과 룰 적용. Day 6 은 잔여만 정리. 부족 시 외부 lib 한정 `ignore_missing_imports` 완화 + W4-v2 첫날 잔여 정리. |
| R12 | 모든 진단 카드 디스클레이머 누락(QA 비용) | 低 | 高 | `DiagnosisResultCard.tsx` 단일 컴포넌트 강제 + Detox e2e 에서 디스클레이머 텍스트 grep 검증. lead/PM Day 4 검수. |

---

## 5. Verification Steps

### 5.1 자동
```bash
cd apps/api
docker compose up -d postgres redis localstack
uv pip install -e ".[dev]"
alembic upgrade head
pytest -v --cov=app --cov-fail-under=80
ruff check .
mypy app                       # 0 errors (AC16)

cd ../ai-server
uv pip install -e ".[dev]"
bash scripts/security/gen_dev_certs.sh   # 자체 서명 인증서
pytest -v --cov=app --cov-fail-under=80
ruff check .
mypy app                       # 0 errors (AC16)
python scripts/eval_vision.py  # AC3
python scripts/eval_audio.py   # AC5

cd ../../packages/shared-types
pnpm codegen
cd ../../apps/mobile
pnpm typecheck                 # AC16
```

### 5.2 수동 (AC13, AC14, AC15)
1. `pnpm -C apps/mobile start` (또는 EAS Build dev client) → 로그인(mock) → 가족 → 펫 선택.
2. 진단 → 카메라 → 4부위 선택 → 촬영 → 업로드 → 결과 카드 + 디스클레이머 확인.
3. 진단 → 오디오 → 카운트다운 → 5–10초 녹음 → 업로드 → 결과 카드 + 디스클레이머 확인.
4. 병원 → 위치 권한 → KakaoMap 위 마커 3개 → 탭 → 상세(전화/주소/진료시간) 확인.
5. 90초 통합 시연 영상 → `.omc/research/w3-v2-demo.mp4`.

### 5.3 종료 점검 (Day 7 PM)
- AC 통과 < 12 → W4-v2 첫날 보강 카드 삽입.
- mypy 0 errors 미달 → W4-v2 첫날 보강.
- 디스클레이머 누락 발견 → 즉시 hotfix(코드 동결 예외).

---

## 6. Team Allocation (4–5인)

| 트랙 | 인력 | 주요 산출 |
|---|---|---|
| Backend Lead (B) | 1 | S3 storage·Diagnose 라우터·DiagnosisEvent·Alembic 0005·Hospital nearby PostGIS·OpenAPI export |
| Backend Dev (B) | 1 | Hospital ETL(data.go.kr + 카카오 지오코딩)·shared-types codegen·devices/auth/uploads 잔여·테스트 픽스처 |
| Mobile Dev (C) | 1 | 카메라 화면·오디오 화면·병원 화면·DiagnosisResultCard·api/diagnose.ts·시연 영상 |
| AI/Infra (A) | 1 | vision.py·audio.py·로컬 AI 서버 mTLS+HMAC·fine-tune+eval·룰 기반 fallback·시연 시드 데이터 |
| Lead/PM (D, 5명일 때) | 1 | 데이터셋 라이선스·디스클레이머 카피·수의사 자문·W4-v2 카드 분해·디스클레이머 검수·Kanban |

> 4명 운영 시 Lead/PM 역할을 Backend Lead 가 겸직, 시연 영상은 Mobile Dev 가 촬영. 데이터셋 라이선스 검수는 AI/Infra 가 1차, lead 가 최종 sign-off.

---

## 7. File Map

```
apps/ai-server/
  app/inference/vision.py                                 [new: MobileNetV3 + ConvNeXt fallback + Mock]
  app/inference/audio.py                                  [new: YAMNet + PANN fallback + Mock]
  app/inference/fallback.py                               [new: 룰 기반 5s timeout fallback]
  app/inference/disease.py                                [edit: 시계열 경로 deprecated — Phase 2 부활 검토]
  app/inference/nutrition.py                              [edit: 시계열 경로 deprecated — Phase 2 부활 검토]
  app/api/v1/vision.py                                    [new: POST /infer/vision]
  app/api/v1/audio.py                                     [new: POST /infer/audio]
  app/schemas/{vision,audio}.py                           [new]
  app/security/hmac_auth.py                               [new: X-AI-HMAC]
  app/security/mtls.py                                    [new: cert verify]
  scripts/train_vision.py                                 [new]
  scripts/train_audio.py                                  [new]
  scripts/eval_vision.py                                  [new]
  scripts/eval_audio.py                                   [new]
  scripts/security/gen_dev_certs.sh                       [new]
  data/skin/                                              [new: train/val split]
  data/audio/                                             [new]
  data/demo/{skin_redness.jpg, eye_discharge.jpg,
              ear_inflam.jpg, gum_paleness.jpg,
              cough_5s.wav, breath_irreg_8s.wav}          [new: 시연 시드]
  tests/test_vision_infer.py                              [new]
  tests/test_audio_infer.py                               [new]
  tests/test_auth.py                                      [new: mTLS+HMAC]

apps/api/
  alembic/versions/0005_multimodal_diagnosis.py           [new]
  app/models/diagnosis_event.py                           [new]
  app/models/hospital.py                                  [edit: location PostGIS POINT]
  app/integrations/storage/{__init__,s3,mock,factory}.py  [new]
  app/integrations/ai_server/{__init__,real,mock,factory}.py [new]
  app/integrations/kakao/local.py                         [edit or new: 지오코딩 fallback]
  app/api/v1/uploads.py                                   [new: presign]
  app/api/v1/diagnose.py                                  [new: image/audio/list]
  app/api/v1/hospitals.py                                 [edit: nearby PostGIS]
  app/services/diagnose.py                                [new]
  seeds/disease_labels.json                               [new]
  seeds/hospitals_seoul.json                              [edit: 50건 정적 시드 갱신]
  tests/test_uploads.py                                   [new]
  tests/test_diagnose.py                                  [new]
  tests/test_hospitals.py                                 [edit: nearby + ETL fallback]
  tests/test_e2e_diagnose.py                              [new: presign → diagnose 흐름]

apps/mobile/
  app/diagnose/_layout.tsx                                [new]
  app/diagnose/camera.tsx                                 [new]
  app/diagnose/audio.tsx                                  [new]
  app/hospitals/index.tsx                                 [new]
  src/api/diagnose.ts                                     [new: uploadAndDiagnose]
  src/api/hospitals.ts                                    [new]
  src/components/DiagnosisResultCard.tsx                  [new]
  src/components/RecordingIndicator.tsx                   [new]
  src/components/KakaoMapView.tsx                         [reuse: W1 spike]
  src/permissions/{camera,audio}.ts                       [new]
  e2e/diagnose.spec.ts                                    [new: Detox/Maestro]

infra/etl/
  hospital_sync.py                                        [edit: LOCALDATA → data.go.kr 1줄 + 카카오 지오코딩 fallback]
  tests/test_hospital_sync.py                             [edit: geocode fallback 케이스]

packages/shared-types/                                    [edit: diagnosis, upload, hospital nearby]

scripts/datasets/skin_download.sh                         [new]
scripts/datasets/audio_download.sh                        [new]

docs/
  ai/vision-eval-w3.md                                    [new: AC3 결과]
  ai/audio-eval-w3.md                                     [new: AC5 결과]
  data/dataset-licenses-w3.md                             [new]
  copy/medical-disclaimer-ko.md                           [new]
  w3-v2-retrospective.md                                  [new, Day 7]
  w3-camera-demo.md                                       [new]
  w3-audio-demo.md                                        [new]
  api/openapi-w3-v2.json                                  [generated, Day 7]

.omc/plans/w4-v2-triage-dashboard-demo.md                 [new, Day 6 초안 → Day 7 finalize]
.omc/plans/open-questions.md                              [edit or new: W3-v2 미결 누적]
.omc/research/w3-camera-demo.mp4                          [new]
.omc/research/w3-audio-demo.mp4                           [new]
.omc/research/w3-hospital-demo.mp4                        [new]
.omc/research/w3-v2-demo.mp4                              [new, Day 7 통합]

docker-compose.yml                                        [edit: localstack, ai-server 서비스]
```

---

## 8. Done Definition

- [ ] AC1~AC16 중 ≥ 12개 통과(목표 13~14).
- [ ] mypy 0 errors (apps/api + apps/ai-server), ruff 0 errors, coverage ≥ 80% (AC16).
- [ ] shared-types codegen 적용, mobile typecheck 통과 (AC16).
- [ ] 90초 W3-v2 통합 시연 영상 1회.
- [ ] `.omc/plans/w4-v2-triage-dashboard-demo.md` 초안 존재.
- [ ] `docs/w3-v2-retrospective.md` 작성.
- [ ] 모든 진단 카드 의료적 디스클레이머 노출 검수 통과.
- [ ] 데이터셋 라이선스 표 검수 + sign-off.
- [ ] CI green (`.github/workflows/{api,ai-server,mobile}.yml`).

---

## 9. Open Questions

1. **Kaggle "Dog's skin diseases" 라이선스 정확 카테고리** — 페이지에 CC0 명시인지, 별도 약관인지 Day 1 다운로드 시점에 확정 필요. 상업/챌린지 사용 가능성 1차 검수는 lead/PM. (R1 직결)
2. **MobileNetV3-Small vs ConvNeXt-Tiny 최종 채택** — Day 3 평가 결과로 결정. AC3 70% 임계 미달 시 ConvNeXt-Tiny 로 1줄 swap. PM 결정 게이트 필요.
3. **YAMNet TF/HF port vs PANN AudioSet** — Day 2 호환성 검증 후 Day 3 최종 채택. 16kHz mono resample 표준 경로 결정(librosa vs torchaudio).
4. **로컬 AI 서버 RTX 5090 가용성 + Cloudflare Tunnel 가용성** — Day 2 mTLS handshake 시점에 검증. 미가용 시 클라우드 GPU 임시 임대 또는 mock 강제 운영 결정 필요.
5. **수의사 자문 시점** — W3-v2 안에서 1차 큐레이션, W4-v2 Day 1~2 자문 review 의무. 자문 위촉 채널(개인 네트워크 vs 학회/온라인 컨설팅) lead/PM 결정.
6. **data.go.kr 통합 인허가 OpenAPI 정확한 endpoint URL + 활용신청 승인 일정** — Day 1 spike 에서 확보. 미발급 시 정적 50건 시드로 AC11/AC12 통과(본선 전 swap).
7. **S3 vs 자체 스토리지(MinIO 등)** — 챌린지 단계는 AWS S3 가정. 비용/리전(서울 ap-northeast-2) 결정. mock-first 유지로 미정 상태에서도 진행 가능.
8. **EAS Build dev client 빌드 일정** — W2-v2 푸시 토큰과 합쳐 Day 1 빌드. 빌드 실패 시 expo-go 한정 시연 + 갤러리 fallback 결정.
- AnimalCLAP GitHub 저장소 (`github.com/dahlian00/AnimalCLAP`) 는 LICENSE 파일 미명시 — Day 1 spike 에서 저자에 issue 등록(MIT 가정하고 진행) + 본선 전 라이선스 명시 확보. HF 모델은 MIT 명시되어 있어 우선 사용 가능.

---

## 10. Changelog

- 2026-05-04 — 초안 작성. W2-v2 freeze 가정(`CARETAIL_POLLING_ENABLED=false` 기본), W3 anomaly+budget+hospital 스코프를 카메라/오디오 멀티모달 진단 + 병원 매칭으로 전면 교체. MobileNetV3-Small + YAMNet 1차 채택, ConvNeXt-Tiny + PANN fallback. data.go.kr 통합 인허가 OpenAPI 채택(LOCALDATA 폐쇄 반영). 모든 진단 카드 의료적 디스클레이머 의무. W4-v2(triage + dashboard + demo) 카드 분해는 Day 6~7 산출.
