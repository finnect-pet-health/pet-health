# W3-v2 데이터셋 라이선스 노트

> AC3 (vision) / AC5 (audio) 학습·평가에 사용할 외부 데이터셋의 라이선스 +
> 다운로드 출처를 일원 정리. 본선 단계 사업계획서 § 데이터 출처 단락에 인용.
>
> 작성일: 2026-05-07 (head-start). 실 다운로드 + sign-off 는 W3-v2 Day 1
> 트랙 A (AI/infra) + lead/PM 협업.

---

## 1. Vision (이미지 진단)

### 1.1 Kaggle "Dog's skin diseases (Image Dataset)"

| 항목 | 내용 |
|---|---|
| 출처 | https://www.kaggle.com/datasets (검색: "dog skin diseases") |
| 다운로드 스크립트 | `scripts/datasets/skin_download.sh` (Day 1, AI/infra) |
| 추정 라이선스 | **TBD** — Kaggle 페이지에 별도 명시 필요. CC0/CC BY/별도 약관 가능. Day 1 다운로드 시점 lead/PM 1차 검수 의무 (R1) |
| 비용 | 무료 (Kaggle 계정 + API token) |
| 샘플 수 | 약 3,000장 (8 클래스, 클래스 불균형) |
| 사용 범위 | 챌린지 단계 fine-tune + 평가. 상업 사용은 라이선스 검수 후 결정 |

**액션**:
- Day 1 다운로드 후 페이지 라이선스 정보를 본 문서 § 1.1 에 transcribe.
- CC0 또는 명확한 사용 허가 부재 시 → § 1.2 fallback 채택.

### 1.2 Fallback — Roboflow Open Images "dog" + 자체 촬영 100장

| 항목 | 내용 |
|---|---|
| Open Images | Apache-2.0 라이선스. 다운로드 무료, 상업 사용 허용. |
| 자체 촬영 | PM/lead 자체 스마트폰 촬영. 자체 자산 → 라이선스 issue 없음 |
| Augmentation | albumentations (MIT) — flip / rotate / colorjitter / cutout |

---

## 2. Audio (오디오 진단)

### 2.1 Kaggle dog cough datasets

| 항목 | 내용 |
|---|---|
| 출처 | Kaggle "Dog cough sound" / "Pet vocalization" 등 1~3개 묶음 (Day 1 검수) |
| 추정 라이선스 | **TBD** — 페이지별 상이. CC BY, ODbL, 별도 약관 가능 |
| 샘플 수 | 합산 ~500–1000개 (5초 미만 ~5초 클립) |

### 2.2 ESC-50 (Environmental Sound Classification)

| 항목 | 내용 |
|---|---|
| 출처 | https://github.com/karolpiczak/ESC-50 |
| 라이선스 | **CC BY-NC 3.0** (Creative Commons Attribution-NonCommercial 3.0). 학술/연구 용도 허용. **상업 사용 금지** — 본선 진출 시 별도 데이터 확보 필요 |
| 사용 범위 | "dog" 라벨 (40 샘플) 만 추출. 챌린지 단계 fine-tune 학습 데이터 보강 |
| 인용 의무 | 논문 인용: Piczak, K. J. (2015). *ESC: Dataset for Environmental Sound Classification*. ACM MM 2015 |

> ⚠ NC 라이선스 — 본 코드베이스가 **상업 product 의 학습 데이터** 로 사용
> 되는 시점 (본선 통과 후) 부터는 ESC-50 제거 + 자체 녹음 / 라이선스 명확
> 한 대체 데이터로 swap 의무.

### 2.3 자체 녹음 50–100건

| 항목 | 내용 |
|---|---|
| 출처 | PM/lead/팀원 본인의 반려동물 또는 친지 동물 녹음 (동의 후) |
| 라이선스 | 자체 자산 — 라이선스 issue 없음. 본선 단계 dataset card 에 출처 명시 |

### 2.4 AnimalCLAP encoder (frozen)

| 항목 | 내용 |
|---|---|
| 출처 (HF) | `risashinoda/animalclap` — HuggingFace 모델 카드 명시 **MIT** |
| 출처 (GitHub) | https://github.com/dahlian00/AnimalCLAP — LICENSE 파일 부재 (issue 등록 대상, draft `.omc/drafts/animalclap-license-issue.md`) |
| 사용 범위 | encoder weights frozen 추론 + MLP head 자체 학습. weights 파일 상업 사용 시 본선 전 LICENSE 확정 필요 |
| 학습 인용 | spike 검증: `apps/ai-server/scripts/spike_animalclap.py` (2026-05-07) |

---

## 3. Sign-off 체크리스트 (W3-v2 Day 1 EOD)

- [ ] Kaggle Dog skin diseases 라이선스 확인 → § 1.1 갱신 (R1)
- [ ] Kaggle Dog cough 라이선스 페이지 visit → § 2.1 갱신
- [ ] ESC-50 인용 필드 본선 사업계획서 § 데이터 출처 단락에 추가
- [ ] AnimalCLAP GitHub LICENSE issue 등록 (`.omc/drafts/animalclap-license-issue.md` 본문 사용)
- [ ] 자체 녹음 동의서 양식 lead 작성 (1 페이지)
- [ ] PM 최종 sign-off 서명 (이름/날짜)

---

## 4. 변경 이력

- 2026-05-07 — v1 작성 (head-start). 실 다운로드 전 사양 정리.
