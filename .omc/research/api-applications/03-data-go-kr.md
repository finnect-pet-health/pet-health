# 03. data.go.kr — 공공데이터포털 동물병원 OpenAPI

| 항목       | 내용                         |
|-----------|------------------------------|
| 우선순위   | **High** (병원 매칭 핵심)    |
| 담당자     | (채울 것)                    |
| 현재 상태  | ✅ **승인 완료 + endpoint 검증 완료 (2026-05-07)** |

---

## 상태 이력

- [x] 회원가입 완료
- [x] 활용신청 완료
- [x] **승인 완료** (2026-05-07)
- [x] **API 호출 검증 완료** (2026-05-07, totalCount=10,516건 수신)

---

## 계정 정보

| 항목        | 값                                          |
|------------|---------------------------------------------|
| 포털 이메일 | (사용자 GitHub 동일 이메일)                  |
| 인증키 위치 | `.env` → `DATA_GO_KR_API_KEY` (Decoding 키) |

---

## ✅ 검증된 호출 정보

### Endpoint
```
https://apis.data.go.kr/1741000/animal_hospitals/info
```

### Dataset
- **ID**: 15154952
- **이름**: 행정안전부\_동물\_동물병원 조회서비스
- **제공기관**: 행정안전부
- **데이터 갱신**: 일일

### 호출 파라미터
| 파라미터    | 필수 | 설명 |
|-----------|------|------|
| serviceKey | ✅   | Decoding 키 (`DATA_GO_KR_API_KEY` 환경변수) |
| pageNo     | ✅   | 페이지 번호 (1부터 시작) |
| numOfRows  | ✅   | 페이지당 행 수 (최대 1000 권장) |
| type       | ✅   | "json" (XML 기본 → 명시적 json 권장) |

### 응답 필드 (검증된 실제 응답 기준)

```json
{
  "response": {
    "body": {
      "totalCount": 10516,
      "numOfRows": 1000,
      "pageNo": 1,
      "items": {
        "item": [
          {
            "BPLC_NM": "브라이튼안과치과동물병원",
            "ROAD_NM_ADDR": "서울특별시 양천구 신월로 338, 태성빌딩 3층",
            "LOTNO_ADDR": "서울특별시 양천구 신정동 1026-1",
            "ROAD_NM_ZIP": "08086",
            "TELNO": "02-2039-0039",
            "SALS_STTS_NM": "영업/정상",
            "DTL_SALS_STTS_NM": "정상",
            "CLSBIZ_YMD": "",
            "LCPMT_YMD": "2026-02-25",
            "CRD_INFO_X": "187415.922905255",
            "CRD_INFO_Y": "446600.184140953",
            "LCTN_AREA": "224.55",
            "MNG_NO": "314000001020260001",
            "OPN_ATMY_GRP_CD": "3140000"
          }
        ]
      }
    }
  }
}
```

### 한국어 필드 매핑
| 응답 필드          | 의미              | 비고 |
|-------------------|-------------------|------|
| `BPLC_NM`         | 사업장명(병원명)   | |
| `ROAD_NM_ADDR`    | 도로명주소         | |
| `LOTNO_ADDR`      | 지번주소           | |
| `ROAD_NM_ZIP`     | 우편번호           | |
| `TELNO`           | 전화번호           | |
| `SALS_STTS_NM`    | 영업상태           | "영업/정상" / "폐업" / "휴업" |
| `CLSBIZ_YMD`      | 폐업일자           | 빈값=영업중 |
| `LCPMT_YMD`       | 인허가일자         | YYYY-MM-DD |
| `CRD_INFO_X/Y`    | TM 좌표           | **EPSG:5174 (Bessel TM 중부원점) → WGS84 변환 필요** |
| `MNG_NO`          | 관리번호 (고유 ID) | upsert key |
| `OPN_ATMY_GRP_CD` | 인허가관청 코드    | |

---

## API 호출 주의사항

### 좌표계 변환

`CRD_INFO_X/Y` 는 **EPSG:5174 (Bessel TM 중부원점)** 좌표.
카카오맵·Web 지도는 **WGS84 (EPSG:4326)** 사용 → 반드시 변환.

```python
from pyproj import Transformer
t = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)
lng, lat = t.transform(187415.922905255, 446600.184140953)
# → (126.85..., 37.52...) 양천구 신월로
```

### Decoding vs Encoding 키

공공데이터포털은 키를 두 종류로 제공:
- **Encoding 키** (URL 인코딩됨) — 브라우저 주소창 복붙용
- **Decoding 키** (원본 문자열) — 코드에서 `httpx params=` 또는 `requests params=` 에 사용

`.env` 의 `DATA_GO_KR_API_KEY` 는 **Decoding 키** 로 입력 완료.

### 정확한 endpoint suffix `/info`

검증 시도 결과:
- BASE 단독 → `500 Unexpected errors`
- `/getAnimalHospitalList`, `/animal_hospitalsList` 등 → `404 API not found`
- **`/info`** → ✅ 정상 응답
- 다른 행안부 OpenAPI 들도 `/info`, `/list`, `/all` 등 짧은 suffix 사용 패턴

---

## ETL 통합 상태

`infra/etl/hospital_sync.py` 갱신 완료 (2026-05-07):
- `fetch_page()`: 실 endpoint + 페이지네이션 구현
- `is_active()`: 영업/정상 필터
- `transform_row()`: 응답 → 내부 schema 매핑 (좌표 변환은 W3-v2 D5)
- `upsert_rows()`: NotImplementedError (Hospital 모델·PostGIS·pyproj 추가 후)

### 실행 명령
```bash
# Dry-run (전체 fetch, DB 미저장)
python -m infra.etl.hospital_sync

# 첫 페이지만
python -m infra.etl.hospital_sync --pages 1

# DB upsert 활성화 (W3-v2 Day 5+ 부터)
python -m infra.etl.hospital_sync --upsert
```

---

## Fallback 계획

- **서울 강남 50개 정적 시드** — W3-v2 plan 의 미발급 시나리오 fallback
- 현재 키 발급 + endpoint 검증 완료로 fallback 불필요. 다만 외부 API 다운 시 정적 시드로 graceful degradation.

---

## 다음 액션

> **W3-v2 Day 5 (5.19 화)** — `Hospital` 모델 + Alembic 0005 + PostGIS POINT 컬럼 + pyproj 의존성 추가 + `upsert_rows()` 구현 + cron 스케줄.
> 그때까지 추가 사용자 액션 없음.
