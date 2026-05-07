# 04. FatSecret — 음식 영양 데이터 API

| 항목       | 내용                      |
|-----------|--------------------------|
| 우선순위   | **Mid** (영양 분석 기능)  |
| 담당자     | (채울 것)                 |
| 현재 상태  | 신청 안 함                |

---

## 상태 이력

- [ ] 신청 안 함
- [ ] 등록 완료 (날짜: )
- [ ] Consumer Key / Secret 발급 (날짜: )
- [ ] 거절 또는 제한 (날짜: )

---

## 계정 정보

| 항목             | 값                                    |
|----------------|---------------------------------------|
| 계정 이메일      | (등록 시 사용한 이메일)                |
| 계정 ID          | -                                     |
| Consumer Key    | `.env` → `FATSECRET_CONSUMER_KEY`     |
| Consumer Secret | `.env` → `FATSECRET_CONSUMER_SECRET`  |

---

## 신청 일자

> 미입력 — 등록 후 채울 것

---

## 신청 채널

- URL: https://platform.fatsecret.com/register
- 방법: 이름, 이메일, 앱 이름, 사용 목적 입력 후 즉시 발급
- 앱 정보:
  - 앱 이름: `PetFinect`
  - 사용 목적: "반려동물 사료·간식 영양 정보 조회 (해커톤 출품작)"

---

## 신청 시 첨부 자료

- 별도 첨부 불필요 (폼 입력만으로 즉시 발급)
- 앱 이름과 사용 목적 텍스트만 입력

---

## 응답 예상 시간

**즉시** (보통) — 이메일로 Consumer Key / Secret 즉시 수령

---

## 인증 방식 주의사항

### OAuth 1.0a HMAC-SHA1

FatSecret API는 **OAuth 1.0a HMAC-SHA1** 서명 방식을 사용함.

```python
# 올바른 서명 방식
import hmac, hashlib, base64, urllib.parse

# PLAINTEXT 방식은 지원하지 않음 — HMAC-SHA1 필수
signature_method = "HMAC-SHA1"
```

> **PLAINTEXT 서명 방식 미지원** — 반드시 HMAC-SHA1로 구현해야 함.
> 라이브러리: `requests-oauthlib` 또는 수동 서명 구현.

```python
from requests_oauthlib import OAuth1Session

fatsecret = OAuth1Session(
    client_key=os.getenv("FATSECRET_CONSUMER_KEY"),
    client_secret=os.getenv("FATSECRET_CONSUMER_SECRET"),
)
response = fatsecret.get("https://platform.fatsecret.com/rest/server.api", params={
    "method": "foods.search",
    "search_expression": "chicken",
    "format": "json",
})
```

---

## 데이터 커버리지 한계

- 한국 음식 커버리지: 부분적 (주요 식품 포함, 전통 음식 일부 누락)
- **펫 사료 / 간식**: 빈약 가능성 높음 — 자체 시드로 보강 필요
- 보강 계획: 자체 200건 한국 펫 사료 시드 데이터 (`src/data/seed/pet-foods-200.json`)

---

## Fallback 계획

- **자체 200건 펫 사료 시드** — FatSecret 미발급 시 또는 데이터 빈약 시 사용
- 정적 영양 데이터 파일로 주요 사료 브랜드·간식 커버
- FatSecret 발급 후에도 펫 사료는 시드 우선 사용, 일반 식품은 FatSecret 호출

---

## 다음 액션 (오늘 — 2026-05-07)

> **오늘 안으로 platform.fatsecret.com/register 접속 → 등록 → Consumer Key/Secret `.env` 입력.**
> 즉시 발급이므로 5분 내 완료 가능. (블로커 낮음, 카카오/data.go.kr 후 처리 가능)
