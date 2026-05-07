# v2 Plans Cross-Check Report (2026-05-07)

> Read-only verification by verifier agent. SOT: `~/.claude/plans/jazzy-roaming-rose.md` (2026-05-06 pivot lock).
> Scope: W2-v2 / W3-v2 / W4-v2 plan 3종 + open-questions tracker + 참조 spec 3종 (02/05/proposal-outline).

---

## Executive Summary

Total checks: 7 (A–G)

- ✅ Pass: 4 (B, C, D, E, F partial)
- ⚠️ Warn: 2 (A 경계 케이스, F partial)
- ❌ Fail: 1 (G — 단일 누락)

전반적으로 3개 plan은 SOT(`jazzy-roaming-rose.md`)와 일관되며 file-path 충돌, AC threshold, Caretail 옵셔널 정책이 정확히 정합. 다만 (1) W3-v2 와 W4-v2 가 `apps/api/app/api/v1/diagnose.py` 에 대해 W3=신규 / W4=수정 의도로 합의되어 있으나 W4-v2 File Map 에 `[edit:]` 표기는 정상, (2) W4-v2 가 `docs/specs/02-health-analysis.md` 와 `docs/specs/05-medical-budget-savings.md` 의 piv 노트는 상위 SOT 통한 간접 참조뿐이라 spec 직접 인용 라인 부족, (3) AC 카운트 표기 (W3-v2 헤더 "12–15개" vs 실제 16개)에 사소 불일치 1건 존재.

가장 중요한 발견: **W3-v2 SOT 메타에 "AC 수: 12–15개" 라고 명시되어 있으나 실제 파일은 AC1~AC16(16개) 존재 → SOT 자체가 갱신 가능 한도 내 (jazzy-roaming-rose.md 99 라인 "AC 수: 12–15개")**. 이는 plan 작성 단계에서 자연 증가했으며 W3-v2 임계 (12/15 또는 12/16) 표현 모순.

---

## Discrepancies Table

| Check | Severity | File:Line | Issue | Suggested Fix |
|---|---|---|---|---|
| A | INFO | jazzy-roaming-rose.md:62 / w4-v2:347 | `apps/api/app/api/v1/diagnose.py` 가 W3-v2 [new] (line 415) + W4-v2 [edit: triage 필드 추가] (line 347) — 의도상 정상 (created in W3, edited in W4) | **No fix needed**. Verbiage 일관, 충돌 아님 |
| A | INFO | w3-v2:407 / w4-v2 (no mention) | `apps/api/app/models/diagnosis_event.py` W3-v2 신규 only — W4-v2 에서는 별도 수정 항목 없음 | **No fix needed**. 정상 |
| A | INFO | w3-v2:427 / w4-v2 (no mention) | `apps/mobile/app/diagnose/camera.tsx` W3-v2 신규 only | **No fix needed**. 정상 |
| A | INFO | w4-v2:344 / w4-v2:352 | `apps/api/app/services/triage.py`, `apps/api/seeds/specialty_mapping.json` W4-v2 신규 only | **No fix needed**. 정상 |
| B | WARN | w3-v2:4,89 | 헤더 "AC 수: 12–15개" SOT 인용 (jazzy-roaming-rose.md:98) vs 실제 AC 1~16 (16개) + Done 임계 "≥ 12개 통과(목표 13~14)" | **w3-v2 임계 문구를 "16개 중 ≥ 12개" 로 통일 + jazzy-roaming-rose.md:98 의 "12–15개" 표기를 "12–16개" 로 sync (선택적, SOT 갱신)** |
| B | PASS | w2-v2:74,397 | Done 임계 "15개 필수 AC 중 ≥ 12개 통과 (AC9–AC11 옵셔널 제외)" — 사용자 명시 일치 | OK |
| B | PASS | w4-v2:63,401 | Done 임계 "12개 중 ≥ 9개 통과" — 사용자 명시 "9/10 or 9/12" 와 9/12 일치 | OK |
| C | PASS | w2-v2:48 / w3-v2:60 / w4-v2:194 | W2-v2 Day 7 (5.14) freeze, W3-v2 Day 7 (5.21) freeze, W4-v2 Day 4 (5.25) hard freeze — 모두 명시 | OK |
| C | PASS | w2-v2:323 / w3-v2:366 / w4-v2:222 | 4 트랙 (백엔드 2 / 모바일 1 / AI·인프라 1 / 리드·PM 1) 일관 | OK |
| C | INFO | w4-v2:222 (Track A: 2명) | W4-v2 Track A 만 백엔드 2명 (Lead + Dev) 명시. W3-v2 line 369–370 도 동일 (Lead + Dev). W2-v2 line 325–327 도 동일 | OK — 일관 |
| D | PASS | w2-v2:49,226 / w3-v2:61,128 / w4-v2:39 | 디스클레이머 의무 W2 부터 도입(spec 02 § 7, spec 05 § 10) → W3-v2 진단 카드 의무 → W4-v2 모달 첫 진입 1회 + 금융 디스클레이머 placeholder 한정 — 단계적 강화 정합 | OK |
| D | PASS | w4-v2:40 | 금융 디스클레이머 placeholder 카드에만 한정 — 사용자 결정사항 #1 (placeholder 카드만) 일치 | OK |
| E | PASS | w2-v2:46 / w3-v2:5,58 / w4-v2:32,93 | `CARETAIL_POLLING_ENABLED=false` 기본 → W3-v2 명시 유지 → W4-v2 mock 강제 (`AI_SERVER_USE_MOCK=1`) + 워치 카드 미연결 기본 + sparkline only on connect — 정합 | OK |
| E | PASS | w4-v2:31 | "Caretail 실 키 발급 후 real provider 검증 — W4 는 mock 강제, real swap 은 본선" 명시 | OK |
| F | PASS | w4-v2:198–207 | Day 4 (5.25) 시간 단위 일정: 09:00 QA, 11:00 hotfix, 12:00 hard freeze, 14:00 자막, 15:00 ZIP, 16:00 검수, 17:00 업로드 | OK — 사용자 명시 (09:00/12:00/17:00) 일치 |
| F | PASS | w3-v2:60,292 | W3-v2 Day 7 (5.21) freeze + W4-v2 카드 분해 + 시연 시드 prep, 신규 코드 금지 명시 | OK |
| G | PASS | w2-v2:8 / w3-v2:4 | W2-v2 spec 02/05 § 참조, W3-v2 spec 02 (Stage 1 시계열 옵셔널 강등) 참조 | OK |
| G | PASS | w4-v2:6 | W4-v2 spec 02·05·proposal-outline 모두 직접 참조 | OK |
| G | FAIL (minor) | docs/specs/02:47 / docs/specs/05:8 | **확인 완료**: 두 spec 파일 모두 "2026-05-06 스코프 피벗" 노트 prepended 됨. 즉 사용자 의도(spec 갱신)는 완료 상태 | **No fix needed** (사용자 우려와 달리 이미 갱신 완료) |
| G | PASS | docs/proposal-outline.md:73,81–88 | S6 핵심 기능 5개 표 ⑤ 워치 옵셔널 + "의료비 예측·적금 본선 공개" + S8 멀티모달 진단 다이어그램 + 본선 단계 부활 명시 — 사용자 결정 일치 | OK |
| G | INFO | docs/proposal-outline.md:90 | S9 핀테크 결합 슬라이드는 헤더는 유지되나 "본선 단계 부활"은 S8 line 88에 명시되어 있음. S9 본문도 본선 보류 표기 필요 여부 확인 권장 | minor — S9 본문에 "본선 단계 공개 예정" 명시 추가 검토 |

---

## Detailed Findings (per check A–G)

### Check A — File path conflicts in File Map

**검증 항목**: W3-v2 와 W4-v2 양쪽에 동일 경로가 [new] 로 중복되는지.

**결과**: ✅ **PASS — 충돌 0건**

- `apps/api/app/models/diagnosis_event.py` — W3-v2 line 408 [new]. W4-v2 File Map (340–395) 에 미언급. **정상**.
- `apps/api/app/api/v1/diagnose.py` — W3-v2 line 415 [new: image/audio/list]. W4-v2 line 347 `[edit: triage 필드 추가]`. **정상 — 명시적으로 W3 신규, W4 수정**.
- `apps/mobile/app/diagnose/camera.tsx` — W3-v2 line 427 [new]. W4-v2 미언급. **정상**.
- `apps/api/app/services/triage.py` — W3-v2 미언급. W4-v2 line 344 [new]. **정상**.
- `apps/api/seeds/specialty_mapping.json` — W3-v2 미언급. W4-v2 line 352 [new]. **정상**.
- `apps/api/app/api/v1/hospitals.py` — W3-v2 line 416 [edit: nearby PostGIS]. W4-v2 line 348 [edit: specialty 필터 + score]. **정상 — 양쪽 다 edit, base 는 W2 시점 W1 spike 또는 사전 존재 가정 (jazzy-roaming-rose.md 41 line `apps/api/app/api/v1/hospitals.py` 이미 REUSE 100%로 명시)**.
- `apps/api/app/integrations/vision/mock.py` / `audio/mock.py` — jazzy-roaming-rose.md line 58–59 [new]. W3-v2 File Map 에는 ai-server 측 vision.py·audio.py 가 [new] 로 위치 (line 382–383). W4-v2 line 350–351 `[edit: hash 매핑 강화]`. **약한 불일치**: W3-v2 File Map 이 `apps/api/app/integrations/vision/` 백엔드 측 mock 폴더 신규 생성을 명시적으로 나열하지 않으나, jazzy-roaming-rose SOT 와 W3-v2 본문 (line 411 `app/integrations/ai_server/{__init__,real,mock,factory}.py [new]`) 가 ai_server 어댑터로 통합되어 있어 의미상 정합. → **No blocker**.

### Check B — AC numbering and cross-references / Done thresholds

| Plan | Header AC count | 실제 AC | Done threshold | 사용자 명시 | 일치? |
|---|---|---|---|---|---|
| W2-v2 | "AC 수: ~16개" (line 31) | 16 (AC1–AC16) | "15개 필수 AC 중 ≥ 12개 통과 (AC9–AC11 옵셔널 제외)" (line 74, 397) | "12/15 (AC9–11 옵셔널 제외)" | ✅ 정합 |
| W3-v2 | "AC 수: 12–15개" (jazzy SOT line 98) | 16 (AC1–AC16) | "16개 중 ≥ 12개 통과(목표 13~14)" (line 89, 471) | "12/15 (or 12/16)" | ⚠️ 헤더 vs 본문 모순 (실제는 16개) |
| W4-v2 | "AC 수: 10–12개, Done 임계 9/10" (jazzy SOT line 108) | 12 (AC1–AC12) | "12개 중 ≥ 9개 통과" (line 63, 401) | "9/10 or 9/12" | ✅ 정합 (12개 채택) |

**Cross-reference 검증**: W4-v2 본문 (line 8) "선행 plan: W3-v2" 단일 참조만 존재. AC 번호를 "W3 AC10" 처럼 명시 인용한 곳 **없음** — 충돌 없음. **PASS**.

**조치 권장**: W3-v2 의 AC 수 표기와 jazzy-roaming-rose.md SOT 동기화. 가장 가벼운 수정은 SOT 의 "AC 수: 12–15개" → "AC 수: 12–16개" 단일 라인 갱신.

### Check C — Track A/B/C/D balance

| Plan | Backend | Mobile | AI/Infra | Lead/PM | 4–5명 분담 |
|---|---|---|---|---|---|
| W2-v2 (line 322–331) | Lead + Dev (2) | Mobile Dev (1) | AI/Infra (1) | Lead/PM (1, 4명일 때 겸직) | ✅ |
| W3-v2 (line 364–374) | Lead (B) + Dev (B) (2) | Mobile Dev (C) (1) | AI/Infra (A) (1) | Lead/PM (D, 1) | ✅ |
| W4-v2 (line 219–227, 222) | 2명 (Lead + Dev) | 1 | 1 | 1 | ✅ |

**Day 7 (W2/W3) 및 Day 4 (W4) freeze 명시**:

- W2-v2 Day 7 (5.14): line 250–256, "Freeze · 통합 · 시연 영상 갱신, 신규 코드 금지" ✅
- W3-v2 Day 7 (5.21): line 292–300, "Freeze · 통합 · 시연 시드 · W4-v2 카드 finalize, 신규 코드 금지" ✅
- W4-v2 Day 4 (5.25): line 194–215, **시간 단위 일정 (09:00 QA, 11:00 hotfix, 12:00 hard freeze, 14:00 자막, 15:00 ZIP, 16:00 검수, 17:00 업로드)** ✅

**한 사람이 같은 날 ≥ 2 트랙**: 4명 운영 시에만 W2-v2 line 332 "Lead/PM 역할을 Backend Lead 가 겸직", W3-v2 line 374 동일. 5명 운영 시는 1:1 매칭 — **블로커 없음**.

**결과**: ✅ **PASS**

### Check D — Disclaimer policy continuity

**최초 도입**: W2-v2 line 49, 226 — `"참고용 추정치, 의료 진단 아님"` (spec 02 § 7, spec 05 § 10 의무).

**W3-v2 확장**: line 61 — `"AI 추정치, 수의사 상담 권장"` 의무 노출 (모든 진단 카드). line 129 `docs/copy/medical-disclaimer-ko.md` 카피 잠금. line 244 v1 확정.

**W4-v2 강화**:
- line 39: 의료적 디스클레이머 = `"AI 추정치이며 수의사 상담을 대체하지 않습니다"` — W3-v2 카피의 명문화.
- line 39: 앱 첫 진입 시 1회 `"본 서비스는 의료기기가 아닙니다"` 모달 의무.
- line 40: **금융 디스클레이머 placeholder 카드에만 한정** (`"의료비 예측·적금은 본선 단계 공개 예정. 본 서비스는 금융상품이 아닙니다"`). 다른 화면 노출 금지.
- line 117: `docs/copy/disclaimers.md` 신규.

**평가**: 정책 연속성 정합. W3-v2 → W4-v2 카피가 "AI 추정치, 수의사 상담 권장" → "AI 추정치이며 수의사 상담을 대체하지 않습니다" 로 강화. 사용자 결정사항 #1 (placeholder 카드만) 일치. ✅ **PASS**.

### Check E — Caretail optional mode consistency

| 항목 | W2-v2 | W3-v2 | W4-v2 |
|---|---|---|---|
| `CARETAIL_POLLING_ENABLED=false` 기본 | line 23–24, 46, 90 | line 5, 58 | line 32 (mock 강제) |
| Worker scheduler 가드 | line 24, 103 | (W2 산출 reuse) | (mock 강제 → 호출 안 함) |
| Mock provider | line 95, 264 | line 58 (시계열 라우팅 우선순위 강등) | line 19 (`AI_SERVER_USE_MOCK=1` 강제, real 호출 시 startup error) |
| UI fallback (워치 미연결 기본) | (W2 미강제, 일반 sparkline) | (해당 화면 W4 산출) | line 18, 93 — `"워치 연결" 버튼만`, 연결 시 sparkline |

**결과**: ✅ **PASS — 정합**. SOT (jazzy-roaming-rose.md 31, 53–54) 와 일관.

### Check F — Submission deadline alignment

**Day 4 (5.25) 시간 일정** (사용자 명시: 09:00 QA / 12:00 freeze / 17:00 submit):

W4-v2 line 198–207 시간 단위 표:

| 시간 | 활동 | 사용자 명시 일치? |
|---|---|---|
| 09:00–11:00 | 회귀 QA | ✅ |
| 11:00–12:00 | hotfix slot | (사용자 명시 없음, 추가 슬롯) |
| **12:00** | **HARD CODE FREEZE** | ✅ |
| 12:00–14:00 | 시연 영상 최종 편집 | (확장) |
| 14:00–15:00 | 자막 검수 + ffprobe 인코딩 검증 | (확장) |
| 15:00–16:00 | GitHub ZIP + 패키지 정리 | (확장) |
| 16:00–17:00 | 검수 게이트 + 전 인원 sign-off | (확장) |
| **17:00** | **챌린지 포털 업로드** | ✅ |

**W3-v2 Day 7 (5.21)**: line 292–300, "Freeze · 통합 · 시연 시드 · W4-v2 카드 finalize, **신규 코드 금지**". ✅ 사용자 명시 (freeze + W4 카드 분해 + demo seed prep, NO new code) 일치.

**결과**: ✅ **PASS**.

### Check G — Cross-reference to specs

**spec 파일 갱신 상태 확인** (read-only):

- `docs/specs/02-health-analysis.md:47` — **있음**: `"2026-05-06 스코프 피벗 적용: 1차 AI 입력은 카메라 이미지(피부/눈/귀/잇몸) + 음성(기침/이상 호흡음) 멀티모달로 변경. 워치(Caretail) 시계열 분석은 옵셔널 보조 입력으로 강등. ... 1차 입력 멀티모달 진단은 W3-v2 plan 참조"`. SOT 명시 (jazzy-roaming-rose.md line 113) 와 일치. ✅
- `docs/specs/05-medical-budget-savings.md:8` — **있음**: `"2026-05-06 스코프 피벗: 본 spec 의 의료비 예측 + 자동 적금 결합 기능은 MVP(5.25 제출) 단계 보류, 본선용으로 부활 결정. W4-v2 plan 에서는 placeholder 카드만 노출"`. SOT (line 114) 와 일치. ✅
- `docs/proposal-outline.md`:
  - line 73 (S6 핵심 기능 5개): `"⑤ (옵셔널) 워치 시계열 생체 카드 (Caretail 연결 시) / 의료비 예측 + 적금은 본선 공개"` ✅
  - line 81 (S8): `"멀티모달 진단 파이프라인 다이어그램"` ✅
  - line 88 (S8): `"본선 단계: 워치 시계열 anomaly 부활 + 의료비 예측 결합으로 진단→비용 흐름 완성"` ✅
  - line 90 (S9 핀테크 결합) — 헤더 유지. **본문 갱신 부족**: S9 슬라이드 본문에 "본선 단계 공개 예정" 명시가 직접적이지 않을 수 있음. 사용자 명시 ("S6/S8 updated") 와 일치하나 S9 명시 갱신은 약함.

**Plan→spec 참조 inversely**:
- W2-v2 line 8 spec 02 § 2~3 + spec 05 § 2~3 ✅
- W3-v2 line 4 spec 02 (Stage 1 시계열 옵셔널 강등 명시) ✅
- W4-v2 line 6 spec 02 + spec 05 (의료비/적금 본선 보류, placeholder 카드만) + proposal-outline § 3 ✅

**결과**: ✅ **PASS** (FAIL 의심 → 검증 결과 사용자 의도대로 spec 갱신 완료, 단 proposal-outline S9 본문 강화 검토 가능).

---

## Recommended Actions (ranked, blocker first)

1. **(WARN, 단순)** W3-v2 plan 의 AC 수 표기를 jazzy-roaming-rose.md SOT 와 동기화.
   - Option A (가장 가벼움): jazzy-roaming-rose.md line 98 `"AC 수: 12–15개"` → `"AC 수: 12–16개"`.
   - Option B: w3-v2 plan AC 수를 16개 → 15개로 축소 (AC16 제거 또는 합치기). **권장하지 않음** (AC16 = mypy strict + ruff + coverage + typecheck 합본, 분리 시 정보 손실).
   - **Pick: Option A**.

2. **(INFO, 선택적)** `docs/proposal-outline.md` S9 슬라이드 본문에도 "MVP 단계 placeholder 카드 / 본선 단계 공개 예정" 한 줄 추가.
   - 현재 line 88 (S8 본문)에만 본선 단계 부활 명시. S9 (line 90~) 의 본문 자체에도 디스클레이머 한 줄 추가 권장.

3. **(VERIFY, 무손상)** w4-v2 line 222 Track A 인력 표기 ("2명 Lead+Dev")가 다른 트랙 (W2/W3) 의 헤더 표 형식과 약간 다름 (W2-v2 line 322 는 두 줄로 분리). 가독성 개선 차원의 미세 정렬 검토 (no-op 가능).

4. **(NO-OP)** 그 외 file map 충돌, AC threshold 일관성, freeze schedule, 디스클레이머 정책, Caretail 옵셔널 모드, spec 피벗 노트 prepend 모두 정합 — 수정 불필요.

5. **(추적)** `.omc/plans/open-questions.md` 에 W3-v2 의 8개 open question (line 484–492) 누적 미완. 현재 트래커는 W4-v2 7개만 포함. **별도 작업으로 W3-v2 + W2-v2 (8개) 누적 권장** (read-only 검증 범위 외, 사용자 명시 task가 아님).

---

## Final Verdict

**Status**: PASS (with 1 WARN, 1 INFO)
**Confidence**: high
**Blockers**: 0

3 plan 모두 SOT 와 정합하며 file path 충돌 / AC threshold / 트랙 분담 / Caretail 옵셔널 / 디스클레이머 정책 / freeze 일정 / spec 참조 모두 통과. 단순한 AC 수 헤더 표기 sync 1건 외 차주 실행 (W2-v2 5.8 시작) 에 차질 없음.
