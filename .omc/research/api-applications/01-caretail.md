# 01. Caretail — 반려동물 건강 데이터

| 항목       | 내용                          |
|-----------|------------------------------|
| 우선순위   | ~~Critical~~ → **프로젝트 제외 (2026-05-07)** |
| 담당자     | (해당 없음)                  |
| 현재 상태  | ❌ **프로젝트에서 제외** |

---

## 상태 이력

- [x] **2026-05-07 — 프로젝트에서 완전 제외 결정** (사용자 결정)
- [ ] ~~신청 안 함~~
- [ ] ~~신청 중~~
- [ ] ~~승인 완료~~
- [ ] ~~거절~~

---

## 제외 사유

사용자 판단 (2026-05-07):
- 파트너십 응답 가능성 낮음 (수일~수주 대기)
- MVP 일정(5.25 마감) 안에 실 통합 어려움
- 멀티모달(카메라+음성) 입력으로 워치 의존도 자체가 낮아짐

## 영향 범위

- W2-v2: 트랙 A Caretail RealProvider stub 작업 삭제, AC9–11+16 삭제
- W3-v2: 옵셔널 워치 sparkline 카드 삭제
- W4-v2: 통합 대시보드 4섹션 → 3섹션 (이미지/오디오/식이)
- spec 02: 3-stage 시계열 파이프라인 deprecated
- `.env` / `.env.example`: `CARETAIL_*` 환경변수 주석 처리

## 코드 자산 재활용

`apps/api/app/integrations/health/` (W1 산출물) 코드는 **유지**:
- `HealthProvider` Protocol → `ImageInferenceProvider` / `AudioInferenceProvider` 와 같은 패턴으로 재활용
- `MockHealthProvider` → 시연용 결정성 mock 으로 유지 가능
- `HealthSnapshot` 모델 → W3-v2 의 `image_s3_ref`, `audio_s3_ref`, `inference_metadata` 컬럼 추가 후 진단 데이터 저장용으로 재활용

> 코드 삭제는 W1 freeze 보호 위해 안 함. dead Caretail-specific 코드(`apps/api/app/integrations/health/real.py` 같은 스텁)는 W2-v2 끝날 때 별도 정리.

## 본선/Phase 2 부활 시

본선(8.28) 또는 Phase 2 단계에서 디바이스 재선정 가능. 그때 다시 이 파일을 활성 상태로 되돌릴 것:
- 다른 워치 옵션 후보: Fitbit, Whistle, Tractive, FitBark, PetPace 등
- 또는 자체 BLE 디바이스 PoC

## References

- 이전 spike 문서: `docs/spikes/caretail-spike.md` (W1 산출물, 보존)
- SOT: `~/.claude/plans/jazzy-roaming-rose.md` (사용자 결정 #4)
- W2-v2 changelog: 2026-05-07 entry
