# Spike · 케어테일(CareTail) 반려동물 워치 API 통합

> **문서 목적**: W1 Day 3-4 산출물 (AC10). 실 API 키 발급 전, 공개 정보 범위 내에서 OAuth 절차·응답 스키마·rate limit·폴링 주기를 최대한 정리하고, RealHealthProvider 구현에 필요한 사전 결정을 문서화한다.
>
> **작성일**: 2026-05-03 (Day 3)
> **상태**: 키 미발급. 공식 API 문서 비공개. Mock 우회 운영 중.
> **담당**: AI/인프라 트랙

---

## 1. 목적

이 스파이크의 결론으로 결정할 것:

1. **인증 방식** — OAuth 2.0 가능 여부, 없을 경우 API Key 방식 여부
2. **폴링 주기** — 5분 / 15분 / 1시간 중 MVP에서 안전한 선택
3. **Rate-limit 정책** — 429 응답 처리 전략 (jitter exponential backoff)
4. **폴백 전략** — 키 미발급 기간 동안 MockHealthProvider 유지 방침
5. **응답 스키마 추정** — HealthSnapshot 필드별 매핑 가능성

현재 공식 API 문서가 외부에 공개되어 있지 않으므로, 유사 펫 IoT API(Fitbit, Garmin, Withings) 패턴을 참고 기준으로 삼는다. 케어테일 고유 정보는 키 발급 후 NDA 범위 내에서 보완한다.

---

## 2. 공식 정보 출처 정리

### 2.1 케어테일 공식 채널

| 출처 | URL | 확인된 정보 |
|---|---|---|
| 케어테일 공식 홈 | https://caretail.net/ | 서비스 소개, 제품(S2+) 설명. 개발자 포털 없음 |
| Google Play 앱 | https://play.google.com/store/apps/details?id=kr.com.peachbite.app.peachbiteapp_kr | 개발사: PeachBite(피치바잇). 패키지명: `kr.com.peachbite.app.peachbiteapp_kr` |
| 피치바잇 공식 홈 | https://peachbite.pet/ | TLS 인증서 만료 확인 불가 (2026-05-03 시점). 사이트 접근 불가 |

**결론**: 2026-05-03 시점 기준, 외부에 공개된 개발자 문서·API 포털·SDK 레퍼런스 없음. B2B 파트너십 문의 채널을 통한 별도 신청이 필요한 구조로 추정됨.

### 2.2 유사 펫 IoT / 웨어러블 API 참조

| 플랫폼 | 인증 | Rate Limit | 폴링 주기 | 출처 |
|---|---|---|---|---|
| **Fitbit** | OAuth 2.0 (PKCE 지원) | 150 req/hr/user | 15분~1시간 권장 (웹훅 우선) | https://dev.fitbit.com/build/reference/web-api/ |
| **Garmin** | OAuth 2.0 (OAuth 1 → 2 마이그레이션 중) | 미공개 (엔터프라이즈 협의) | Push(Ping/Pull) 또는 Webhook | https://developer.garmin.com/gc-developer-program/health-api/ |
| **Withings** | OAuth 2.0 | 120 req/min (엔터프라이즈 상향 가능) | 폴링 or Webhook | - |

---

## 3. OAuth 통합 절차 (확인된 만큼)

### 3.1 인증 방식

**[추정]** 케어테일 공식 OAuth 문서는 현재 비공개. 동종 펫 IoT API 패턴 기반으로 두 가지 시나리오를 상정한다.

**시나리오 A — OAuth 2.0 Authorization Code + PKCE (권장 추정)**

```
1. 사용자가 앱 내 "케어테일 연동" 버튼 클릭
2. 앱 → caretail.net/oauth/authorize?client_id=...&redirect_uri=...&scope=...&code_challenge=...
3. 사용자 케어테일 계정 로그인 및 동의
4. 케어테일 → redirect_uri?code=AUTH_CODE
5. 백엔드 → POST caretail.net/oauth/token
   body: { grant_type: "authorization_code", code, redirect_uri, client_id, client_secret }
   응답: { access_token, refresh_token, expires_in, token_type: "Bearer" }
6. access_token → API 호출 헤더: Authorization: Bearer {access_token}
7. 만료 시: POST /oauth/token { grant_type: "refresh_token", refresh_token }
```

**시나리오 B — API Key 방식 (단순화된 파트너 전용)**
- 파트너십 승인 후 client_id + secret 쌍을 발급받아 고정 헤더로 사용
- 사용자 동의 흐름 없음 → 대신 디바이스 페어링 코드 방식 가능성

### 3.2 redirect_uri 설정

**[추정]** 모바일 앱 딥링크 스키마 (`petfinect://oauth/caretail/callback`) 또는 백엔드 콜백 URL (`https://api.petfinect/v1/auth/caretail/callback`) 등록 필요. 승인 전 사전 등록 요구 예상.

### 3.3 토큰 수명 (추정)

| 토큰 | [추정] 수명 | 근거 |
|---|---|---|
| access_token | 1~2시간 | Fitbit 1h, Garmin 유사 패턴 |
| refresh_token | 30~90일 | 대부분 IoT API 30일 이상 |
| 갱신 방식 | refresh_token rotation | 보안 표준 패턴 |

> 실제 수명은 키 발급 후 응답 헤더 `expires_in` 필드로 확인 필수.

---

## 4. Endpoint 응답 스키마 (예상 5개)

케어테일 공식 스키마 미공개. 아래는 HealthSnapshot (§ 2.2) 필드 매핑을 위한 추정 엔드포인트다. Fitbit Web API 인트라데이 패턴을 참고 기준으로 사용.

### EP-1 · 활동 데이터 `[추정]`

```
GET /v1/pets/{device_id}/activity?since={iso8601}&until={iso8601}
Authorization: Bearer {token}

응답 (추정):
{
  "device_id": "abc123",
  "period_start": "2026-05-03T00:00:00Z",
  "period_end":   "2026-05-03T05:00:00Z",
  "activity": {
    "active_minutes": 47,          // → HealthSnapshot.activity_min
    "steps": 3210,
    "calories_burned": 185,
    "distance_m": 2100
  }
}
```

HealthSnapshot 매핑: `activity.active_minutes` → `activity_min`

### EP-2 · 심박 데이터 `[추정]`

```
GET /v1/pets/{device_id}/heartrate?since={iso8601}&until={iso8601}
Authorization: Bearer {token}

응답 (추정):
{
  "device_id": "abc123",
  "heartrate": {
    "avg_bpm": 82,                 // → HealthSnapshot.hr_avg
    "min_bpm": 58,                 // → HealthSnapshot.hr_min
    "max_bpm": 134,                // → HealthSnapshot.hr_max
    "resting_bpm": 65,
    "zones": [
      { "name": "rest",   "minutes": 180 },
      { "name": "active", "minutes": 47  }
    ]
  }
}
```

HealthSnapshot 매핑: `heartrate.avg_bpm` / `min_bpm` / `max_bpm`

### EP-3 · 수면 데이터 `[추정]`

```
GET /v1/pets/{device_id}/sleep?date={YYYY-MM-DD}
Authorization: Bearer {token}

응답 (추정):
{
  "device_id": "abc123",
  "sleep": {
    "total_min": 420,
    "stages": {
      "awake_min": 30,             // → sleep_state 판정용
      "light_min": 210,
      "deep_min": 180
    },
    "efficiency": 0.88
  }
}
```

HealthSnapshot 매핑: `stages.deep_min / total_min` 비율로 `sleep_state` Enum 산출
- deep ratio ≥ 0.35 → `'deep'`, ≥ 0.15 → `'light'`, else → `'awake'`

### EP-4 · 체중 데이터 `[추정]`

```
GET /v1/pets/{device_id}/weight?date={YYYY-MM-DD}
Authorization: Bearer {token}

응답 (추정):
{
  "device_id": "abc123",
  "weight_kg": 8.2,                // → HealthSnapshot.weight
  "measured_at": "2026-05-03T07:30:00Z",
  "source": "scale"                // 일부 케어테일 모델은 스마트 저울과 연동
}
```

HealthSnapshot 매핑: `weight_kg` → `weight`

### EP-5 · 통합 스냅샷 `[추정]`

```
GET /v1/pets/{device_id}/snapshot?since={iso8601}
Authorization: Bearer {token}

응답 (추정 — 이상적인 단일 엔드포인트):
{
  "device_id": "abc123",
  "snapshots": [
    {
      "ts": "2026-05-03T05:00:00Z",
      "activity_min": 47,
      "hr_avg": 82,
      "hr_min": 58,
      "hr_max": 134,
      "sleep_stage": "light",
      "weight_kg": 8.2,
      "quality": 0.91
    }
  ]
}
```

> 단일 스냅샷 엔드포인트 존재 여부는 불확실. EP-1~EP-4 개별 호출 후 어댑터에서 병합하는 방식으로 설계.

---

## 5. Rate Limit / Polling 정책

### 5.1 일반적인 펫 IoT API Rate Limit 패턴

| 플랫폼 | Limit | 초과 응답 | 리셋 |
|---|---|---|---|
| Fitbit | 150 req/hr/user | 429 + `Retry-After` 헤더 | 매 정각 |
| Withings | 120 req/min | 429 | 1분 슬라이딩 |
| Garmin | 비공개 (엔터프라이즈) | 429 | 미공개 |
| **케어테일 [추정]** | **50~150 req/hr/user** | **429** | **매 정각 (추정)** |

케어테일은 소규모 스타트업이므로 Fitbit 대비 더 엄격한 제한(50 req/hr) 적용 가능성을 보수적으로 가정.

### 5.2 5분 폴링의 가능성/리스크

사용자 1명당 5분 폴링 시 호출 수 계산:

- EP-1~EP-4 각 1회씩 = **4 req / 5분 = 48 req/hr/user**
- EP-5 단일 엔드포인트 존재 시 = **12 req/hr/user**

보수적 추정(50 req/hr/user)에서도 **4-endpoint 방식은 96%를 소진**하므로 위험.
단일 스냅샷 엔드포인트(EP-5) 존재 시 12 req/hr로 여유 확보.

**리스크 요약**:
- 비용/트래픽 기준 케어테일이 더 낮은 한도 적용 가능
- 멀티 엔드포인트 방식에서 5분 폴링은 rate limit 소진 위험
- 워치 자체 동기화 주기가 15분 이상이면 5분 폴링은 의미 없는 중복 호출

### 5.3 백오프 전략 (429 시)

```python
import random, asyncio

async def fetch_with_backoff(fn, max_retries=5):
    base_delay = 60  # 초 (rate limit reset 주기 가정)
    for attempt in range(max_retries):
        try:
            return await fn()
        except RateLimitError as e:
            retry_after = e.retry_after or base_delay
            jitter = random.uniform(0, retry_after * 0.2)
            delay = min(retry_after * (2 ** attempt) + jitter, 3600)
            await asyncio.sleep(delay)
    raise MaxRetriesExceeded()
```

---

## 6. MVP 폴링 주기 결정

### W1 Day 3-4 결정: **15분 폴링 채택**

| 주기 | req/hr/user (4-EP) | 판정 |
|---|---|---|
| 5분 | 48 | 보수적 한도(50) 거의 소진. 위험 |
| **15분** | **16** | 여유 충분. 워치 동기화 주기와 일치 가능성 높음 |
| 1시간 | 4 | 안전하나 데이터 시의성 부족 |

**근거**:
1. 케어테일 S2+ 워치는 15분 단위 배치 동기화 추정 (일반 BLE 펫 워치 패턴).
2. 15분 간격 = 4 req × 4 = 16 req/hr → 50 req/hr 한도의 32% 사용, 안전 마진 확보.
3. spec § 2.1의 "5분 윈도 활동 분"은 서버측 집계 윈도우이며, 폴링 주기와 별개로 유지 가능.
4. 실 키 수령 후 rate limit 확인되면 5분으로 단축 또는 1시간으로 보수화 재검토.

**Celery beat 설정 초안**:
```python
CELERYBEAT_SCHEDULE = {
    "caretail-poll": {
        "task": "tasks.health.poll_caretail",
        "schedule": crontab(minute="*/15"),
    }
}
```

---

## 7. RealHealthProvider 구현 스켈레톤 (Pseudo)

파일 위치: `apps/api/app/integrations/health/real.py`

```python
"""
RealHealthProvider — 케어테일 API 실 연동.
키 발급 전: 이 파일은 스켈레톤만 존재. factory.py는 MockHealthProvider를 반환.
키 발급 후: CARETAIL_CLIENT_ID / CLIENT_SECRET / BASE_URL 환경변수 채우고
             factory.py의 분기를 수정.
"""

from __future__ import annotations
import os
from datetime import datetime
from uuid import UUID
import httpx

from app.integrations.health import HealthProvider, HealthSnapshot
from app.security.token_store import get_caretail_token, refresh_caretail_token


class RealHealthProvider:
    """Protocol: HealthProvider"""

    BASE_URL: str = os.getenv("CARETAIL_BASE_URL", "https://api.caretail.net")  # [추정]

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        self._client = http_client or httpx.AsyncClient(timeout=10.0)

    # -----------------------------------------------------------------
    # Public interface (HealthProvider Protocol)
    # -----------------------------------------------------------------
    async def fetch_window(
        self, pet_id: UUID, since: datetime
    ) -> list[HealthSnapshot]:
        device_id = await self._resolve_device_id(pet_id)
        token = await self._get_valid_token(pet_id)

        # [추정] 단일 스냅샷 엔드포인트 시도, 없으면 개별 호출로 폴백
        raw = await self._fetch_snapshot(device_id, since, token)
        return [self._normalize(s, pet_id) for s in raw]

    # -----------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------
    async def _get_valid_token(self, pet_id: UUID) -> str:
        """access_token 반환. 만료 시 refresh_token으로 갱신."""
        token_info = await get_caretail_token(pet_id)
        if token_info.is_expired():
            token_info = await refresh_caretail_token(
                token_info.refresh_token,
                client_id=os.environ["CARETAIL_CLIENT_ID"],
                client_secret=os.environ["CARETAIL_CLIENT_SECRET"],
            )
        return token_info.access_token

    async def _resolve_device_id(self, pet_id: UUID) -> str:
        """pet_id → 케어테일 device_id 매핑 (DB 또는 캐시)."""
        # TODO: Pet 모델에 caretail_device_id 필드 추가 후 조회
        raise NotImplementedError("키 발급 후 구현")

    async def _fetch_snapshot(
        self, device_id: str, since: datetime, token: str
    ) -> list[dict]:
        """EP-5 단일 스냅샷 엔드포인트 [추정]. 404 시 EP-1~4 병렬 호출로 폴백."""
        url = f"{self.BASE_URL}/v1/pets/{device_id}/snapshot"
        resp = await self._client.get(
            url,
            params={"since": since.isoformat()},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 429:
            raise RateLimitError(retry_after=int(resp.headers.get("Retry-After", 60)))
        resp.raise_for_status()
        return resp.json().get("snapshots", [])

    def _normalize(self, raw: dict, pet_id: UUID) -> HealthSnapshot:
        """케어테일 원시 응답 → HealthSnapshot 정규화 어댑터."""
        return HealthSnapshot(
            pet_id=pet_id,
            ts=datetime.fromisoformat(raw["ts"]),
            source="caretail",
            activity_min=raw.get("activity_min"),
            hr_avg=raw.get("hr_avg"),
            hr_min=raw.get("hr_min"),
            hr_max=raw.get("hr_max"),
            sleep_state=raw.get("sleep_stage"),
            weight=raw.get("weight_kg"),
            raw_blob_ref=None,  # S3 업로드는 폴링 워커에서 처리
            quality=raw.get("quality", 1.0),
        )


class RateLimitError(Exception):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
```

> MockHealthProvider와 동일한 `HealthProvider` Protocol을 만족. factory.py에서 `CARETAIL_USE_MOCK=1` 환경변수로 분기.

---

## 8. 위험 & 대응

| # | 위험 | 확률 | 영향 | 대응 |
|---|---|---|---|---|
| R1 | API 승인 지연 (5.25 시연 전까지 미도착) | 高 | 高 | MockHealthProvider로 시연 전체 커버. 시연 슬라이드에 "공식 연동 신청 진행 중" 디스클레이머 명시 |
| R2 | 공개 API 없음 (B2B NDA 전용) | 中 | 高 | NDA 체결 후 NDA-안전한 엔드포인트·스키마만 코드 주석으로 반영. 스키마 추정 부분 교체 |
| R3 | Rate limit이 예상보다 낮음 (예: 20 req/hr) | 中 | 中 | 폴링 주기를 30분으로 자동 폴백. 단일 스냅샷 EP 우선 협의 |
| R4 | 응답 스키마가 추정과 다름 | 高 | 中 | `_normalize()` 어댑터 레이어가 변경 흡수. HealthSnapshot 필드는 변경 없이 유지 |
| R5 | 워치 동기화 주기 > 폴링 주기 (중복 호출) | 中 | 低 | `ingest_ts` 기준 중복 제거 로직 추가. ETag / Last-Modified 캐싱 활용 |
| R6 | 피치바잇 개발사 응답 없음 | 中 | 高 | 케어테일 공식 홈 contact 폼 + 공모전 참가팀 우대 조항 명시 후 재발송 |
| R7 | OAuth 미지원 (기기 자체 페어링만 가능) | 低 | 高 | BLE 직접 연결 PoC 검토 (Phase 2). MVP는 mock 유지 |

---

## 9. Day 3 시점 결론 (2026-05-03)

### 현 시점 결정

1. **폴링 주기**: 15분 채택 (5분은 rate limit 소진 위험, 1시간은 데이터 시의성 부족).
2. **인증 방식**: OAuth 2.0 Authorization Code + PKCE 방식 우선 가정. 키 발급 후 확인.
3. **MVP 전략**: MockHealthProvider로 5.25 시연까지 커버. RealHealthProvider 스켈레톤은 이미 준비됨.
4. **어댑터 레이어**: `_normalize()` 함수가 스키마 변경을 흡수 → HealthSnapshot 인터페이스는 동결 가능.
5. **단일 스냅샷 EP**: EP-5 단일 엔드포인트 우선 협의 요청. 없으면 EP-1~4 병렬 호출.

### 키 발급 후 즉시 검증할 항목 5개

1. **인증 방식 확인**: OAuth 2.0인지, API Key 방식인지, 디바이스 페어링 방식인지 → `factory.py` 분기 결정.
2. **access_token 수명 확인**: `expires_in` 값 → `token_store.py`의 갱신 트리거 로직 조정.
3. **Rate limit 헤더 확인**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` 헤더 존재 여부 → 폴링 주기 5분 단축 가능 여부 재평가.
4. **실제 응답 스키마 확인**: 추정 EP-1~EP-5 필드명과 실제 일치 여부 → `_normalize()` 어댑터 수정.
5. **단일 스냅샷 엔드포인트 존재 여부**: EP-5 존재 시 req/hr 대폭 절감 → 폴링 주기 단축 가능.

### 본선 전까지 해야 할 추가 작업

| 시점 | 작업 |
|---|---|
| 키 발급 직후 (W2 or W3) | `RealHealthProvider._fetch_snapshot()` 및 `_normalize()` 실 구현 |
| W2 | `Pet` 모델에 `caretail_device_id` 필드 추가 + 디바이스 페어링 UI |
| W2~W3 | OAuth 콜백 라우터 (`GET /v1/auth/caretail/callback`) 구현 |
| W3 | 케어테일 토큰 안전 저장 (KMS 암호화, spec § 2.1 참조) |
| W4 (본선 전) | E2E 폴링 워커 통합 테스트 (실 워치 데이터 1회 수신 확인) |

---

## 참고 자료

- 케어테일 공식 사이트: https://caretail.net/
- 피치바잇(개발사): https://peachbite.pet/ (TLS 만료, 접근 불가 — 2026-05-03)
- Fitbit Web API 레퍼런스: https://dev.fitbit.com/build/reference/web-api/
- Fitbit Intraday 심박 엔드포인트: https://dev.fitbit.com/build/reference/web-api/intraday/get-heartrate-intraday-by-date/
- Garmin Health API 개요: https://developer.garmin.com/gc-developer-program/health-api/
- Wearable API 통합 가이드: https://www.thryve.health/blog/wearable-api-integration-guide-for-developers
- 상위 plan: `.omc/plans/w1-auth-foundation.md` (AC10)
- 헬스 분석 spec: `docs/specs/02-health-analysis.md` (§ 2.1, § 2.2)
