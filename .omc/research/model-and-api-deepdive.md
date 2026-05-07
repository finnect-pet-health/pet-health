# Research · 모델 / 외부 API 심층 조사 (PetFinect)

> **검증 일시**: 2026-05-06
> **목적**: W3·W4 plan 실행 직전, AI 모델·데이터셋·외부 API 의 라이선스/한국어 지원/쿼터/시그니처 흐름을 검증해 swap 가능한 어댑터 결정을 잠근다.
> **상태**: 1차 (외부 검증 가능 정보 위주). 일부 항목은 키 발급 후 재검증 필요(`[검증 필요]` 태그).
> **상위 plan**: `.omc/plans/w3-ai-anomaly-budget-hospital.md`, `.omc/plans/w4-ai-disease-savings-demo.md`

---

## 1. PetBERT / 펫 의료 LM 후보

### 1.1 후보 비교 표

| Rank | HF Model ID | Base | License | 학습 데이터 | 한국어 | 활성도 (DL/30d) |
|---|---|---|---|---|---|---|
| ① | `SAVSNET/PetBERT` | `bert-base-uncased` (110M) | **openrail** | UK 1차 진료 EHR 5.1M, 500M 토큰 (개·고양이) | ❌ 영어 전용 | **3,895** |
| ② | `havocy28/VetBERT` | `Bio_ClinicalBERT` (110M) | **openrail** | VetCompass Australia 15M 레코드, 1.3B 토큰 | ❌ 영어 전용 | 78 |
| ③ | `klue/roberta-base` | RoBERTa-base (110M) | CC-BY-SA-4.0 | KLUE 한국어 코퍼스 | ✅ 한국어 native | 활성 |
| ④ | `monologg/koelectra-base-v3-discriminator` | ELECTRA-base | Apache-2.0 | 한국어 일반 | ✅ | 활성 |
| ⑤ | `NeuML/pubmedbert-base-embeddings` | BERT-base (110M) | Apache-2.0 | PubMed 영어 의료 | ❌ 영어 | 활성 |

### 1.2 라이선스 분석 — `openrail`

- **PetBERT/VetBERT** 둘 다 RAIL family(OpenRAIL-M). 상업 사용 **허용**, 단 use-based restrictions 있음 (의료 진단을 사람에게 직접 제공하는 의료기기 용도 제한).
- PetFinect 는 "AI 추정치, 수의사 상담 권장" 디스클레이머를 의무 노출하므로 OpenRAIL 제한 조항(의료 진단 기기) 회피 가능. **사용 가능 판정**.
- 단, 본선/상용화 시 라이선스 재검토 필요. KB금융 챌린지 출품작 단계는 무난.

### 1.3 한국어 지원 갭과 대응

PetBERT/VetBERT 는 모두 영어 전용 → **한국어 시계열 직렬화 문장**(spec 02 § 3 의 "활동 30%↓, 심박 평균 10%↑")에 직접 fine-tune 불가.

**대응 옵션 (W4 Day 1 spike 결정)**:
1. **하이브리드**: 시계열 → 영어 자연어 직렬화("activity drop 30%, hr +10%") → PetBERT/VetBERT fine-tune. **장점**: 펫 의료 도메인 지식 활용. **단점**: 사용자 노출 라벨은 한국어 매핑 테이블 필요.
2. **한국어 native fallback**: `klue/roberta-base` zero-shot multi-label classification + 한국어 라벨 20종 손큐레이션. **장점**: UI 한국어 자연 노출. **단점**: 도메인 적합성 낮음.
3. **번역 레이어**: 입력만 한국어 → DeepL/구글 번역 → 영어 PetBERT → 결과 라벨만 다시 한국어. **단점**: 추가 외부 의존.

### 1.4 RTX 5090 Fine-tune 적합성

- BERT-base 110M params × LoRA → 1~3GB VRAM 충분 (RTX 5090 32GB).
- PetBERT 원본 학습은 A100 × 450h (논문 기준). LoRA fine-tune 5.25 데모용은 30분~2시간.
- W4 Day 1~2 에 200~500 샘플(LLM augmented) 으로 LoRA 1 epoch 충분.

### 1.5 TL;DR 결정

> **W4 채택안**: 하이브리드 옵션 1. PetBERT 베이스 → 영어 직렬화 + 한국어 라벨 매핑 테이블. Day 1 09:00 1시간 spike 에서 PetBERT 다운로드 + tokenizer 호환 확인. 실패 시 옵션 2(klue/roberta-base zero-shot) 1줄 swap. 구현 추상화는 `apps/ai-server/app/inference/disease_classifier.py` 의 `Classifier(Protocol)` 인터페이스 안에 잠금.

---

## 2. 수의 / 펫 헬스 공개 데이터셋

### 2.1 후보 비교

| Rank | Source | License | Size | Lang | Schema | 적합성 |
|---|---|---|---|---|---|---|
| ① | `karenwky/pet-health-symptoms-dataset` (HF) | **MIT** | 2,000 rows | 영어 | text · condition (5종) · record_type (Owner/Clinical) | 5 conditions 만 — 보강 필요 |
| ② | `gretelai/symptom_to_diagnosis` (HF) | Apache-2.0 (Gretel) | ~1,200 rows | 영어 | symptom → diagnosis | 일반 의료, 펫 미포함 |
| ③ | `infinite-dataset-hub/VetPetCare` (HF) | [검증 필요] | 미공개 | 영어 | patient_id, species, breed, age, symptoms, diagnosis, treatment | 합성 큐레이션, 라이선스 불명 → 사용 보류 |
| ④ | Kaggle "Pet Health Symptoms" (yyzz1010) | CC0 (추정) | 2k rows | 영어 | ① 와 동일 원본 | ① 의 mirror |
| ⑤ | Kaggle "Animal Condition Classification" (gracehephzibahm) | CC0 (추정) | ~870 rows | 영어 | symptom1~5, dangerous (binary) | 다종 동물 일반 분류, 부분 활용 |
| ⑥ | 한국수의통합DB (`vetdb.go.kr` 등) | 비공개/연구용 | [검증 필요] | 한국어 | [검증 필요] | 직접 액세스 필요, 메일 문의 |

### 2.2 데이터 부족 문제와 보강 전략

**문제**: 영어 합성 데이터 위주, 한국어 펫 도메인 자료 부재. spec 02 § 3.5 의 "LLM augmentation" 의무.

**전략 (W4 Day 1)**:
- Base: `karenwky` 2,000 rows (5 conditions) + `Animal Condition` 870 rows.
- Augmentation: GPT-4 / Claude 로 한국어 + 시계열 직렬화 형식으로 5,000 샘플 합성. 라벨 distribution 균형 잡고 수의사 자문 1회 (W4 Day 2).
- 최종: ~8,000 샘플 → train/val 8:2 → LoRA 1 epoch.

### 2.3 TL;DR 결정

> **W4 채택안**: ① karenwky/pet-health-symptoms-dataset (MIT, 즉시 사용) + ⑤ Animal Condition (CC0) → 한국어 LLM augmentation 5,000 샘플 합성 → 수의사 review → final 8k. CSV 시드는 `apps/ai-server/data/disease_seed.jsonl`.

---

## 3. FatSecret Platform API — OAuth 1.0 흐름

### 3.1 핵심 사실

| 항목 | 값 |
|---|---|
| 인증 방식 | **OAuth 1.0a HMAC-SHA1 only** (PLAINTEXT 미지원) |
| Production Base URL | `https://platform.fatsecret.com/rest/server.api` |
| Sandbox URL | [없음, production 만 존재] |
| 가입 URL | `https://platform.fatsecret.com/register` |
| 일일 쿼터 | [검증 필요 — 문서 미공개. 무료 티어 ~5,000 calls/day 추정] |
| Korean 한국 음식 커버리지 | [검증 필요 — `region=KR&language=ko` 파라미터 가능, 실제 펫 사료 빈약 가능성 spec 명시] |
| Premier 유료 티어 | [검증 필요 — 페이지에 가격 공개 안 함, 영업 문의 필요] |

### 3.2 Signature Base String 포맷

```
<HTTP Method>&<Request URL URL-encoded>&<Normalized Parameters URL-encoded>
```

**예시 (FatSecret 공식 문서 발췌)**:
```
POST&https%3A%2F%2Fplatform.fatsecret.com%2Frest%2Fserver.api&a%3Dfoo%26oauth_consumer_key%3Ddemo%26oauth_nonce%3Dabc%26oauth_signature_method%3DHMAC-SHA1%26oauth_timestamp%3D12345678%26oauth_version%3D1.0%26z%3Dbar
```

### 3.3 Python httpx + authlib 샘플 (foods.search Korean)

```python
# apps/api/app/integrations/fatsecret/real.py
import httpx
from authlib.integrations.httpx_client import OAuth1Auth

CONSUMER_KEY = os.environ["FATSECRET_CLIENT_ID"]
CONSUMER_SECRET = os.environ["FATSECRET_CLIENT_SECRET"]
BASE_URL = "https://platform.fatsecret.com/rest/server.api"

async def search_korean_food(query: str) -> list[dict]:
    auth = OAuth1Auth(
        client_id=CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        signature_method="HMAC-SHA1",
        signature_type="QUERY",  # FatSecret 은 query string 에 OAuth params
    )
    params = {
        "method": "foods.search",
        "search_expression": query,           # 예: "닭가슴살"
        "format": "json",
        "region": "KR",
        "language": "ko",
        "max_results": 20,
    }
    async with httpx.AsyncClient(auth=auth, timeout=10.0) as client:
        resp = await client.post(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("foods", {}).get("food", [])
```

> **주의**: FatSecret 은 OAuth params 를 query string 또는 Authorization header 둘 다 허용. authlib `signature_type="QUERY"` 가 호환성 가장 높음.

### 3.4 Korean 음식 / 펫 사료 커버리지

- **사람 음식**: `region=KR` + `language=ko` 로 한국 일반 식품 (닭가슴살, 사과, 김밥 등) 다수 검색 가능 — 사용자 입력 추정 OK.
- **반려견 사료**: spec 02 § 3 의 우려대로 빈약 가능성 큼. **자체 시드 200건** 보강 의무 (W2 plan AC6, `apps/api/seeds/pet_foods.py`).
- 대안: `roboflow/dog-food` 같은 비공식 데이터셋 [검증 필요].

### 3.5 TL;DR 결정

> **W2 채택안**: FatSecret OAuth 1.0a HMAC-SHA1 + authlib `OAuth1Auth(signature_type="QUERY")`. 사람 음식만 FatSecret 사용, 펫 사료는 자체 200건 시드. 키 발급은 `register` 즉시 가능 추정 (timeline 미공개). Day 1 spike 에 1회 `foods.search?q=닭가슴살` 호출 성공 확인.

---

## 4. data.go.kr — 동물병원 데이터셋

### 4.1 ⚠️ 중요 변경사항 (2026-04-16)

- **LOCALDATA(`localdata.go.kr`) 폐쇄됨** (2026-04-16 부). spec 의 "LOCALDATA 수의업" 후보는 **무효**.
- 이후 모든 인허가 데이터는 `data.go.kr` 통합 포털에서 제공.
- 검색 경로: data.go.kr → 데이터검색 → "인허가" → "지방행정인허가데이터".

### 4.2 후보 데이터셋

| Rank | 데이터셋 | URL | 형식 | 갱신 |
|---|---|---|---|---|
| ① | **행정안전부\_동물병원** (날짜 suffix) | `https://www.data.go.kr/data/15045050/fileData.do` | **CSV/XLSX 파일** | 분기 또는 비정기 |
| ② | 행정안전부\_지방행정인허가데이터(통합) | `data.go.kr` 검색 "인허가" | OpenAPI XML | 일일 |
| ③ | 건강보험심사평가원\_병원정보서비스 | `https://www.data.go.kr/data/15001698/openapi.do` | OpenAPI | 월 | (사람 병원이라 동물병원 미포함, 참고용) |
| ④ | 부천시 등 시·구 단위 자체 데이터 | 광역별 | CSV/API | 자체 |

### 4.3 [검증 필요] OpenAPI vs FileData 선택

**문제**: ① "행정안전부\_동물병원" 페이지가 `/fileData.do` 라 OpenAPI 가 아닐 가능성 큼. 일일 cron sync (`infra/etl/hospital_sync.py`) 시:
- **(A) 파일 데이터 다운로드 방식**: `requests.get` 으로 CSV 정기 다운로드 → 파싱 → upsert. 단점: 갱신 주기 길고 좌표 없을 수 있음.
- **(B) 통합 인허가 OpenAPI**: ② 의 통합 OpenAPI 에서 업종코드 = "수의업" 또는 "동물병원" 필터. 실시간성 좋음, 단 정확한 endpoint URL 사용자가 활용신청 후 확인.

**키 발급 후 검증 항목 (Day 1 spike)**:
1. ② 통합 인허가 OpenAPI 의 endpoint URL 확보 (활용신청 페이지 swagger 다운로드).
2. 응답에서 `bizCondNm` 또는 `uptaeCdNm` 같은 업종 필드로 동물병원 필터 가능한지.
3. `lat/lng` 직접 제공 vs 주소만 제공(지오코딩 필요) 확인.

### 4.4 인증키 — Encoding vs Decoding 함정

공공데이터포털은 **Encoding 키**와 **Decoding 키** 두 형태를 같이 제공:

- **Decoding 키**: 원본 키 (특수문자 `+/=` 포함 가능). `httpx.get(params={"serviceKey": DECODING_KEY})` 처럼 **params 딕셔너리**에 넣을 때 사용. httpx/requests 가 알아서 URL-encode.
- **Encoding 키**: 이미 URL-encode 된 키 (`%2B%2F%3D` 등). **URL 문자열에 직접 박을 때** 사용 (`f"...?serviceKey={ENCODING_KEY}&..."`).

**규칙**: `params=` 딕셔너리 사용 → **Decoding 키**. URL string concat → **Encoding 키**. 잘못 섞으면 401/403 + 디버깅 시간 손실.

### 4.5 응답 형식

- 기본 **XML** 응답. 명시적으로 `&_type=json` 또는 `&dataType=JSON` 파라미터 필요 (데이터셋마다 다름).
- 페이징: `numOfRows`(페이지당) + `pageNo`(현재 페이지) + 응답에 `totalCount`.

### 4.6 샘플 코드 (가정 endpoint)

```python
# infra/etl/hospital_sync.py
import httpx

SERVICE_KEY = os.environ["DATA_GO_KR_API_KEY"]  # Decoding 키
ENDPOINT = "https://api.data.go.kr/openapi/tn_pubr_public_animal_hospital_info_api"  # [검증 필요]

async def fetch_page(page_no: int = 1, num_rows: int = 100):
    params = {
        "serviceKey": SERVICE_KEY,    # Decoding 키
        "pageNo": page_no,
        "numOfRows": num_rows,
        "type": "json",
    }
    async with httpx.AsyncClient(timeout=10.0) as c:
        resp = await c.get(ENDPOINT, params=params)
        resp.raise_for_status()
        return resp.json()
```

### 4.7 폴백 (mock-first 유지)

키 미발급 또는 endpoint 검증 실패 시 W3 plan 기준 **서울 강남 50개 동물병원 정적 시드** 사용 (`apps/api/seeds/hospitals_seoul.json`). 좌표는 카카오 로컬 지오코딩 미리 반영.

### 4.8 TL;DR 결정

> **W3 채택안**: Day 1 spike 에서 통합 인허가 OpenAPI 활용신청 + endpoint URL 확보. 발급 즉시 fetch_page() 1회 검증. 실패/지연 시 정적 50개 시드 → AC 통과 후 본선 전 swap. **Decoding 키**를 `params=` 딕셔너리에 넣는 경로로 통일. 좌표 결측 시 카카오 로컬 API 지오코딩 (`KAKAO_REST_API_KEY` 사용).

---

## 5. Open Questions (사용자 결정 필요)

1. **PetBERT openrail 라이선스 use-based 제한** 의 "의료 진단 기기" 조항이 펫 도메인에도 적용되는가? 챌린지 단계는 OK 추정, 본선 통과 후 자문 필요.
2. **한국수의통합DB** 직접 액세스 절차 — 농림축산검역본부 또는 학회 메일 문의 필요. 시간 소요 클 가능성.
3. **FatSecret 일일 쿼터** 비공개 → 등록 후 응답 헤더 확인. Premier 유료 티어 가격 미공개로 본선 단계 BM 계산 어려움.
4. **data.go.kr 동물병원 OpenAPI** 정확한 endpoint URL 확인 — 활용신청 후 swagger 페이지에서 추출. 폐업 식별/좌표 결측 비율 미확정.
5. **수의사 자문 확보 시점** — W4 Day 2 까지 1회 review 의무. 미확보 시 의료적 디스클레이머 가중 노출.

---

## 6. 결론 — W3·W4 플랜 영향

| Plan AC | 영향 |
|---|---|
| W3 AC10 (data.go.kr ETL) | LOCALDATA 폐쇄 반영 → "행정안전부 통합 인허가 OpenAPI" 로 대상 변경 필요 |
| W3 AC11 (50개 mock) | 변경 없음, 폴백 경로 그대로 유효 |
| W4 AC1 (PetBERT fine-tune) | OpenRAIL 사용 가능 판정. Day 1 spike 에서 영어 직렬화 + 한국어 라벨 매핑 테이블 추가 필요 |
| W4 AC1 fallback | klue/roberta-base zero-shot 으로 1줄 swap 경로 잠금 |
| W4 AC4 (스테이지 2 mock) | demo_scenarios.py 결정성 보장 위해 mock provider 강제 (`AI_SERVER_USE_MOCK=1`) |
| W2 AC6 (FatSecret + 200건 시드) | OAuth 1.0a HMAC-SHA1 흐름 확정. authlib `OAuth1Auth(signature_type="QUERY")` 채택 |

→ **W3 plan § 1.1 의 "data.go.kr 동물병원 ETL" 항목에 LOCALDATA 폐쇄 사실 1줄 추가 권장.**

---

## 7. References

- [SAVSNET/PetBERT · Hugging Face](https://huggingface.co/SAVSNET/PetBERT)
- [havocy28/VetBERT · Hugging Face](https://huggingface.co/havocy28/VetBERT)
- [karenwky/pet-health-symptoms-dataset · HF](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset)
- [FatSecret OAuth 1.0 Documentation](https://platform.fatsecret.com/docs/guides/authentication/oauth1)
- [FatSecret Platform Resources](https://platform.fatsecret.com/docs/guides)
- [공공데이터포털 (data.go.kr)](https://www.data.go.kr/)
- [행정안전부\_동물병원\_파일데이터](https://www.data.go.kr/data/15045050/fileData.do)
- [건강보험심사평가원\_병원정보서비스 OpenAPI](https://www.data.go.kr/data/15001698/openapi.do)
- [농림축산식품 공공데이터 포털](https://data.mafra.go.kr/)
- [PetBERT Nature Scientific Reports 2023 — 논문](https://www.nature.com/articles/s41598-023-45155-7)

---

## 8. W3-v2 데이터셋·모델 가용성 검증 (2026-05-07)

> **검증 목적**: W3-v2-multimodal-diagnosis-hospital 플랜 실행(2026-05-15) 전 4개 핵심 에셋의 라이선스·접근성·기술 사양 사전 확인.
> **검증 방법**: WebFetch(공식 페이지 직접), WebSearch(메타데이터 교차 검증). Kaggle 페이지는 로그인 벽으로 인해 일부 항목은 웹 검색 결과 및 관련 논문·코드에서 간접 확인.

---

### 8.1 Kaggle "Dog's Skin Diseases (Image Dataset)" — youssefmohmmed

Kaggle의 개 피부 질환 이미지 분류 데이터셋. 2024~2025년 수의 AI 논문 다수에서 베이스라인으로 인용.

| 항목 | 값 | 비고 |
|---|---|---|
| **라이선스** | **CC BY-SA 4.0** (추정) | Kaggle 기본 정책상 작성자가 별도 지정 없으면 CC BY-SA 4.0 적용. 페이지 직접 접근 불가로 간접 확인 — **다운로드 후 반드시 라이선스 탭 재확인 필요** |
| **URL** | `https://www.kaggle.com/datasets/youssefmohmmed/dogs-skin-diseases-image-dataset` | |
| **업로드 시점** | 2024~2025 | 관련 논문(IJSDR 2025-07) 인용 확인 |
| **이미지 수** | 미확인 (직접 접근 필요) | 관련 연구에서 "4,053개 이상 개 피부 이미지" 언급 — 동일 데이터셋 여부 미확정 |
| **레이블 카테고리** | 미확인 (직접 접근 필요) | 관련 연구 기준 후보: bacterial dermatosis, fungal infection, hot spot, mange/demodicosis, pyoderma, atopic dermatitis, healthy |
| **이미지 해상도** | 미확인 | |
| **증강 여부** | 미확인 | |

**대안 데이터셋 (백업)**

| 소스 | 라이선스 | 이미지 수 | 클래스 | 비고 |
|---|---|---|---|---|
| Roboflow Universe — litespy/dog-skin-diseases | **CC BY 4.0** (확인됨) | **618장** | bacterial-dermatosis, fungal-infection, healthy, hypersensitivity-allergic-dermatosis, dog-skin-diseases(기타) — 5종 | Object Detection 포맷(bbox), Classification 재변환 필요 |
| Roboflow Universe — dog-skin-disease-dermatosis | 확인 필요 | 미확인 | 미확인 | 별도 workspace |
| Kaggle — yashmotiani/dogs-skin-disease-dataset | 확인 필요 | 미확인 | 미확인 | 2024년 4월 업로드, "best on internet" 자칭 |

**TL;DR 결정**: ⚠️ 검증 필요 — 라이선스 탭을 직접 열어 CC BY-SA 4.0 또는 CC0 여부 확인 필수. 상업적 용도(본선)에서 SA(ShareAlike) 조항은 파생물 동일조건 공개 의무를 수반하므로, CC0 또는 Apache-2.0 레이블 데이터셋을 1차 대안으로 확보 권장. 즉시 사용 가능한 백업: Roboflow litespy (CC BY 4.0 확인, 618장) — 단 규모가 작아 증강 필수.

**Sources**
- [Kaggle 데이터셋 페이지](https://www.kaggle.com/datasets/youssefmohmmed/dogs-skin-diseases-image-dataset)
- [Roboflow Universe — litespy dog-skin-diseases (CC BY 4.0, 618장)](https://universe.roboflow.com/litespy-l22hu/dog-skin-diseases)
- [IJSDR 2025 — Dog Skin Disease Detection using Deep Learning](https://ijsdr.org/papers/IJSDR2507201.pdf)
- [Kaggle — yashmotiani/dogs-skin-disease-dataset](https://www.kaggle.com/datasets/yashmotiani/dogs-skin-disease-dataset)

---

### 8.2 개 기침·발성 오디오 데이터셋

개 기침 및 발성 분류를 위한 오디오 데이터셋. W3-v2 청진/발성 진단 기능의 핵심 훈련 자료.

**1차 후보: Kaggle — ziadelhussein/dog-disease-sound-dataset**

| 항목 | 값 | 비고 |
|---|---|---|
| **라이선스** | 미확인 (로그인 필요) | Kaggle 정책상 CC BY-SA 4.0 기본값 추정 |
| **URL** | `https://www.kaggle.com/datasets/ziadelhussein/dog-disease-sound-dataset` | |
| **카테고리** | 질환별 개 소리 (cough 포함 추정) | 제목에 "disease" 명시 — 기침/건강 이진 분류 가능성 높음 |
| **포맷** | 미확인 | WAV 추정 |
| **클립 수 / 샘플레이트** | 미확인 | 직접 다운로드 후 확인 필요 |

관련 연구(2025 Springer JEET — *Dog Cough Sound Classification Using Neural Networks*): 건강한 개 기침 124건 + 기관지 질환 개 기침 94건 = 총 218건 사용. 규모가 매우 작으므로 증강 또는 추가 수집 필요.

**대안 데이터셋 비교**

| 소스 | 라이선스 | 클립 수 | 포맷 | 특징 |
|---|---|---|---|---|
| HF — ArlingtonCL2/DogSpeak_Dataset | **CC BY-NC-SA 4.0** (확인됨) | **77,202개** bark sequences | WAV | 156마리, 5 breed, bark/noise 분류 — cough 미포함, **비상업적** 제한 |
| HF — ArlingtonCL2/Barkopedia-Dog-Vocal-Detection | 미확인 | 547행 / 6.5 GB | WAV | dog vs dog_noise 이진, cough 구분 없음 |
| HF — cgeorgiaw/animal-sounds | 미확인 | 693 recordings | 미확인 | 성견 10마리, 3 context (disturbance/isolation/play) |
| Kaggle — ESC-50 (환경음 포함) | CC BY-NC 3.0 | 2,000 clips | WAV | dog bark 클래스 포함, cough 없음, **비상업적** |

**TL;DR 결정**: ⚠️ 검증 필요 — 개 기침 전용 공개 데이터셋은 규모가 극도로 작거나(218건) 기침 레이블 자체가 없음. ziadelhussein 데이터셋은 라이선스·내용 직접 확인 후 사용 여부 결정. **상업 허용 + 기침 레이블** 조건을 동시에 만족하는 단일 데이터셋은 현재 미확인. 현실적 대응: (1) ziadelhussein 다운로드 + 라이선스 확인, (2) ESC-50의 dog bark를 proxy로 활용 + 수의사 현장 녹음 50~100건 추가 수집, (3) DogSpeak(77k clip)는 CC BY-NC-SA 4.0으로 비상업적 단계(데모)에서만 사용.

**Sources**
- [Kaggle — dog-disease-sound-dataset (ziadelhussein)](https://www.kaggle.com/datasets/ziadelhussein/dog-disease-sound-dataset)
- [HF — DogSpeak_Dataset (CC BY-NC-SA 4.0, 77,202 clips)](https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset)
- [HF — Barkopedia-Dog-Vocal-Detection (547 rows)](https://huggingface.co/datasets/ArlingtonCL2/Barkopedia-Dog-Vocal-Detection)
- [ACM MM 2025 — DogSpeak 논문](https://dl.acm.org/doi/10.1145/3746027.3758298)
- [Springer JEET 2025 — Dog Cough Sound Classification](https://link.springer.com/article/10.1007/s42835-025-02306-2)
- [Nature Sci. Reports 2023 — BrachySound (개 호흡음)](https://www.nature.com/articles/s41598-023-47308-0)

---

### 8.3 google/mobilenet_v3_small_100_224

경량 이미지 분류 백본. W3-v2 피부 병변 분류 모델의 기본 아키텍처 후보.

HF 페이지(https://huggingface.co/google/mobilenet_v3_small_100_224)는 401 인증 오류로 직접 접근 불가. timm 라이브러리 및 관련 모델 카드로 교차 확인.

| 항목 | 값 | 출처 |
|---|---|---|
| **라이선스** | **Apache-2.0** | timm HF 모델 카드(mobilenetv3_small_100.lamb_in1k) 확인 |
| **파라미터 수** | **2.5M** (2,540,000) | timm 모델 카드, Qualcomm HF 카드 교차 확인 |
| **GMACs** | 0.1 | timm 모델 카드 |
| **입력 해상도** | 224 × 224 | 모델명에 명시 |
| **ImageNet-1k Top-1** | **약 67.2~67.5%** | 관련 구현체(d-li14/mobilenetv3.pytorch) "67.2% MobileNetV3-Small", timm lamb_in1k 변형 기준 |
| **timm 모델 ID** | `mobilenetv3_small_100.lamb_in1k` 또는 `tf_mobilenetv3_small_100.in1k` | timm HF Hub 확인 |
| **PyTorch 호환** | ✅ 완전 호환 | timm `create_model()` API 직접 지원 |
| **fine-tune 방법** | `timm.create_model('mobilenetv3_small_100.lamb_in1k', pretrained=True, num_classes=N)` | timm 공식 문서 |

```python
import timm

# 피부 질환 분류 fine-tune 예시 (N = 클래스 수)
model = timm.create_model(
    'mobilenetv3_small_100.lamb_in1k',
    pretrained=True,
    num_classes=7,   # 예: 7종 피부 질환
)
model.eval()
```

**대안 모델 비교표**

| 모델 | 라이선스 | 파라미터 | ImageNet Top-1 | timm ID | 비고 |
|---|---|---|---|---|---|
| **MobileNetV3-Small** (채택 후보) | Apache-2.0 | **2.5M** | ~67.4% | `mobilenetv3_small_100.lamb_in1k` | 최경량, 모바일 추론 최적 |
| microsoft/resnet-50 | MIT | 25.6M | 80.4% | `resnet50.a1_in1k` | 10× 무거움, 정확도 우수 |
| facebook/convnext-tiny-224 | CC BY-NC 4.0 | 28.6M | 82.1% | `convnext_tiny.fb_in22k_ft_in1k` | **비상업적 제한** — 본선 사용 불가 |

> facebook/convnext-tiny-224의 CC BY-NC 4.0 라이선스는 상업적 용도에서 사용 불가. 본선 출품작에 포함 금지.

**TL;DR 결정**: ✅ 사용 가능 — Apache-2.0 라이선스 확인, 2.5M 파라미터로 엣지 추론 적합, timm 완전 지원. `google/mobilenet_v3_small_100_224` HF ID는 접근 불가였으나 timm ID `mobilenetv3_small_100.lamb_in1k`로 동일 가중치 접근 가능. 대안으로 `resnet50` (MIT) 사용 가능하나 4× 이상 무거워 W3-v2 실시간 진단 요구사항에 불리.

**Sources**
- [timm HF — mobilenetv3_small_100.lamb_in1k](https://huggingface.co/timm/mobilenetv3_small_100.lamb_in1k)
- [timm HF — tf_mobilenetv3_small_100.in1k](https://huggingface.co/timm/tf_mobilenetv3_small_100.in1k)
- [timm 공식 문서 — MobileNet v3](https://huggingface.co/docs/timm/en/models/mobilenet-v3)
- [Qualcomm HF — MobileNet-v3-Small (2.54M params)](https://huggingface.co/qualcomm/MobileNet-v3-Small)
- [d-li14/mobilenetv3.pytorch — 67.2% 재현](https://github.com/d-li14/mobilenetv3.pytorch)

---

### 8.4 YAMNet (오디오 이벤트 분류)

Google의 AudioSet 기반 오디오 이벤트 분류 모델. W3-v2 청진/발성 분석의 feature extractor 후보.

| 항목 | 값 | 출처 |
|---|---|---|
| **라이선스** | **Apache-2.0** | tensorflow/models GitHub 소스 헤더 직접 확인 |
| **공식 TF Hub URL** | `https://tfhub.dev/google/yamnet/1` → Kaggle 모델 페이지로 redirect | TF Hub 302 redirect 확인 |
| **아키텍처** | MobileNet_v1 기반 depthwise-separable CNN | README 및 yamnet.py 직접 확인 |
| **임베딩 차원** | **1024** | yamnet.py GlobalAveragePooling2D 최종 레이어 필터 수 확인 |
| **출력 클래스 수** | **521개** (AudioSet. 원본 527개에서 6개 제거) | README 직접 확인 |
| **파라미터 수** | **3.7M** | README "3.7M weights" 명시 |
| **연산량** | 69.2M multiplies / 960ms 프레임 | README 명시 |
| **Keras 호환성** | ⚠️ Keras 2 전용 — **TF 2.16+ (Keras 3 기본) 비호환** | README 명시 |
| **입력 요구사항** | 16 kHz 모노 WAV, ~10초 단위 처리 | TF Hub 문서 |

**PyTorch 포트 옵션 비교**

| 라이브러리 | 라이선스 | YAMNet 진짜 포트? | 임베딩 차원 | AudioSet 클래스 | 설치 |
|---|---|---|---|---|---|
| `torch-vggish-yamnet` (StefanoGiacomelli) | **MIT** | ✅ YAMNet + VGGish 둘 다 | 1024 (YAMNet 기준) | 지원 (AudioSet ontology 참조) | `pip install torch-vggish-yamnet` |
| `torch_audioset` (w-hc) | **MIT** | ✅ YAMNet + VGGish | 1024 | 지원 | `pip install -e .` (editable) |
| `panns_inference` (qiuqiangkong) | **MIT** | ❌ YAMNet 아님 — PANNs CNN14 계열 | **2048** (CNN14) | **527**개 | `pip install panns-inference` |
| `harritaylor/torchvggish` | MIT | ❌ VGGish만 (YAMNet 아님) | 128 | ❌ | — |

> `harritaylor/torchvggish`는 YAMNet이 아닌 VGGish 전용임. 혼동 주의.

**PANNs CNN14 (`panns_inference`) 별도 평가**

YAMNet 대안으로 비TF 프로젝트에서 주로 사용. 라이선스 MIT, AudioSet 527클래스, mAP 0.431(AudioSet), 임베딩 2048차원, PyTorch >= 1.0 요구. `pip install panns-inference`로 즉시 설치 가능. clip-level tagging + embedding 동시 반환.

```python
# PANNs CNN14 — 개 기침 분류 추론 예시
from panns_inference import AudioTagging

at = AudioTagging(checkpoint_path=None, device='cuda')
(clipwise_output, embedding) = at.inference(audio)
# embedding shape: (batch, 2048)
# clipwise_output: 527 AudioSet class probabilities
```

**YAMNet PyTorch 포트 사용 예시 (torch-vggish-yamnet)**

```python
pip install torch-vggish-yamnet

from torch_vggish_yamnet import yamnet
model = yamnet.YAMNet(pretrained=True)
emb, logits = model(audio_tensor)  # emb shape: (frames, 1024)
```

**TL;DR 결정**: ✅ 사용 가능 (Apache-2.0 확인) — 단, **TF 직접 사용 시 TF <= 2.15 고정 필요** (Keras 3 비호환). 비TF 프로젝트는 `torch-vggish-yamnet` (MIT, 진짜 YAMNet 포트, pip 설치) 채택. 임베딩 차원 1024 확정. `sgugger/dog-cough-classifier`는 HF에서 존재 미확인 — 실제 없는 모델로 판단. 개 기침 특화 분류가 필요하다면 PANNs CNN14 (2048-dim, MIT) fine-tune이 현실적 대안.

**Sources**
- [YAMNet GitHub README (Apache-2.0, 521 classes, 1024-dim)](https://github.com/tensorflow/models/blob/master/research/audioset/yamnet/README.md)
- [YAMNet yamnet.py 소스 (Apache-2.0 헤더 확인)](https://github.com/tensorflow/models/blob/master/research/audioset/yamnet/yamnet.py)
- [TF Hub YAMNet/1 → Kaggle redirect](https://tfhub.dev/google/yamnet/1)
- [torch-vggish-yamnet PyPI (MIT, pip install)](https://pypi.org/project/torch-vggish-yamnet/)
- [StefanoGiacomelli/torch_vggish_yamnet GitHub](https://github.com/StefanoGiacomelli/torch_vggish_yamnet)
- [w-hc/torch_audioset GitHub (MIT)](https://github.com/w-hc/torch_audioset)
- [panns-inference PyPI (MIT, CNN14, 527 classes)](https://pypi.org/project/panns-inference/)
- [qiuqiangkong/panns_inference GitHub](https://github.com/qiuqiangkong/panns_inference)
- [TF 공식 YAMNet 튜토리얼](https://www.tensorflow.org/hub/tutorials/yamnet)

---

### 8.5 종합 결정 요약 (W3-v2 플랜 실행 전)

| # | 에셋 | TL;DR 결정 | 블로커 |
|---|---|---|---|
| 8.1 | Kaggle Dog Skin Dataset (youssefmohmmed) | ⚠️ 검증 필요 | 라이선스 탭 직접 확인 필수. SA 조항 확인 시 Roboflow litespy (CC BY 4.0) 백업 즉시 전환 |
| 8.2 | 개 기침 오디오 데이터셋 | ⚠️ 검증 필요 | 기침 레이블 + 상업 허용 데이터셋 단독 미존재. ziadelhussein 다운 확인 + 현장 녹음 보강 계획 필수 |
| 8.3 | MobileNetV3-Small | ✅ 사용 가능 | 없음. timm ID `mobilenetv3_small_100.lamb_in1k`로 즉시 로드. facebook/convnext-tiny **비상업 제한 주의** |
| 8.4 | YAMNet | ✅ 사용 가능 | TF 버전 고정 필요(≤2.15). 비TF는 `torch-vggish-yamnet` (MIT) 사용. `sgugger/dog-cough-classifier` 존재 미확인 — 사용 불가 |

**W3-v2 Day 1 필수 spike 항목**:
1. Kaggle youssefmohmmed 데이터셋 로그인 후 라이선스 탭 확인 → CC0/CC BY 이면 즉시 채택, SA 이면 Roboflow 백업으로 전환
2. ziadelhussein dog-disease-sound-dataset 다운로드 후 클래스 구조·라이선스 확인
3. `pip install torch-vggish-yamnet` + YAMNet 1024-dim 임베딩 추출 1회 검증
4. `timm.create_model('mobilenetv3_small_100.lamb_in1k', pretrained=True)` 로드 + forward pass 확인

---

## 9. AnimalCLAP 평가 (2026-05-07 추가)

### 9.1 자료 위치

| 자원 | URL | 라이선스 |
|---|---|---|
| 논문 | arXiv `2603.22053` (Shinoda et al., ICASSP 2026) | — |
| 모델 | `huggingface.co/risashinoda/animalclap` | **MIT** (확정) |
| 코드 | `github.com/dahlian00/AnimalCLAP` | ❌ LICENSE 파일 부재 (이슈 등록 필요) |
| 데이터셋 | `huggingface.co/datasets/risashinoda/animalclap-dataset` | "other" — 샘플별 CC-BY/NC 혼합 |
| 자매 데이터셋 (Dog Play Pant) | Zenodo 18972388 | CC-BY-NC-4.0 (사용 불가) |

### 9.2 논문이 예측·검증하는 것

**Task A — Zero-shot Species Recognition** (6,823종, 학습 안 한 300종 unseen 평가):
- AnimalCLAP top-1 **27.6%** / top-5 **53.5%** / mAP **37.6%**
- CLAP baseline top-1 1.61% / top-5 5.19% / mAP 2.73% → **17× 향상**

**Task B — 22 Ecological Trait Inference** (F1 vs CLAP):
- 9 차원 (Diet type / Activity pattern / Locomotion mode·posture / Habitat / Climatic distribution / Social behavior / Predator / Migratory)
- 행동 형질(활동시간 83.7, 이주 84.0, 비행 92.6) 큰 폭 향상, 광역 환경 형질(서식지·기후) 작은 향상

**입력 사양**: 48 kHz 리샘플링, 10초 랜덤 크롭. 인코더 HTS-AT (audio) + RoBERTa (text), CLIP contrastive loss.

### 9.3 PetFinect 적합성 평가

| 활용 | 가능 여부 | 근거 |
|---|---|---|
| 22 traits 직접 활용 | ❌ | 종 레벨 특성 (식이/이동/서식지) — 개체 의료 상태와 무관 |
| 6,823종 분류 직접 활용 | ❌ | 사용자는 이미 "개" 임을 알고 있음 |
| Audio encoder feature extractor 차용 | ✅ | HTS-AT 백본 700K 동물 vocalization 사전학습 → YAMNet (AudioSet 일반) 보다 도메인 가까움 |
| 종 검증 sanity check | ✅ (보조) | 사용자 녹음이 실제 개 소리인지 1차 검증 (사람 기침/생활소음 거르기) |

### 9.4 TL;DR 결정

> **W3-v2 채택안**: AnimalCLAP audio encoder (frozen) + custom MLP head (**512→128→5** 카테고리: 정상/기침/이상호흡/꼬르륵/기타) + LoRA 1 epoch on 자체 녹음 50–100건 + Kaggle 개 기침 데이터. **2026-05-07 spike 검증 완료** — `[1, 512]` L2-normalized 임베딩, 154M params, 590MB checkpoint, CPU 7.4s/5초 클립. GPU sm_75+ 필요. 실패 시 YAMNet (Apache-2.0) 으로 1줄 swap. 데이터셋 risashinoda/animalclap-dataset 은 미사용 (라이선스 혼합 + 도메인 mismatch). Dog Play Pant 는 CC-BY-NC + 도메인 mismatch 로 제외.

### 9.5 References

- [arXiv 2603.22053 — AnimalCLAP](https://arxiv.org/abs/2603.22053)
- [HF model — risashinoda/animalclap (MIT)](https://huggingface.co/risashinoda/animalclap)
- [HF dataset — animalclap-dataset](https://huggingface.co/datasets/risashinoda/animalclap-dataset)
- [GitHub — dahlian00/AnimalCLAP](https://github.com/dahlian00/AnimalCLAP)
- [Project page](https://dahlian00.github.io/AnimalCLAP_Page/)
- [Zenodo 18972388 — Dog Play Pant (제외)](https://zenodo.org/records/18972388)
