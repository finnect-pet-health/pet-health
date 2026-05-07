# Spike · 외부 API 검증 가이드

> 5.25 마감 전까지 5개 외부 통합을 점검·연동하기 위한 신청·키 발급·환경변수 정리.
> **W1(5.1~5.7)에 절대 끝내야 함** — 신청 절차가 길거나 응답이 늦을 수 있는 항목 우선.

## 우선순위 매트릭스

| # | 통합 | 위험 | 첫 통신 시도 마지노선 | 담당 |
|---|---|---|---|---|
| 1 | **케어테일 워치 API** | 가장 높음(승인·계약) | 5.3 | 백엔드 + PM |
| 2 | **카카오 디벨로퍼 (로그인 + 맵)** | 중간(앱 키 즉시) | 5.2 | 모바일 |
| 3 | **공공데이터포털 (동물병원)** | 낮음(키만 발급) | 5.4 | 백엔드 |
| 4 | **FatSecret (영양)** | 중간(승인·강아지 데이터 빈약 가능) | 5.5 | 백엔드 |
| 5 | **오픈뱅킹/적금** | 매우 높음(사업자 필요) | 결정 보류 → 외부 가입 링크 + mock | PM |

---

## 1. 케어테일 워치 API ⚠️ 최우선

**왜 최우선인가**: AI 헬스 분석 전체의 입력. 승인 지연 시 mock provider로 전환할 시간이 필요.

### 액션 플랜
- [ ] 케어테일 공식 홈페이지에서 **개발자/파트너십 문의** 채널 확인 (이메일/폼).
- [ ] 회사 소개 + 본 프로젝트 1-pager(공모전 출품) 첨부 → 데이터 접근 요청 메일 발송.
- [ ] 응답 받기 전: 자체 mock 데이터 시드 동시 진행 (1주일치 합성 데이터, `apps/api/seed/caretail_mock.json`).
- [ ] OAuth 흐름·rate limit·webhook 여부 확인 후 `apps/api/app/integrations/caretail.py` 작성.

### 확인 항목 (메일에 포함)
- 데이터 항목: 활동량(분), 심박(평균/구간), 수면 단계, 체중, 위치(옵셔널)
- 폴링 vs Webhook 지원 여부
- Rate limit, OAuth 스코프, 데이터 보관 기간
- 비상업 학술용 vs 상업용 라이선스 구분
- 사업자 등록 미보유 시 가능한 레벨 (개인 개발자 / 학생 트랙 등)

### 환경변수
```
CARETAIL_CLIENT_ID=
CARETAIL_CLIENT_SECRET=
CARETAIL_BASE_URL=
```

### Fallback
- API 미가용 시 `MockHealthProvider`(시드 데이터) 사용. 인터페이스는 spec 02 §2.1 참고.

---

## 2. 카카오 디벨로퍼 (로그인 + 카카오맵)

**왜 빠르게**: 모바일/백엔드 둘 다 의존. 키 발급은 즉시.

### 절차
1. **카카오 디벨로퍼 콘솔 접속** → 앱 생성.
2. 앱 설정에서 **REST API 키 / Native 앱 키 / JavaScript 키** 확인.
3. **카카오 로그인** 활성화 → 동의 항목(닉네임/이메일/프로필) 설정 → Redirect URI 등록.
4. **카카오맵 SDK** 활성화(JavaScript 키 사용).
5. 앱 패키지명/번들ID 등록 (`app.petfinect`).
6. 비즈 앱 전환은 본선 단계에서 (개인정보 추가 동의 필요 시).

### 환경변수
```
KAKAO_REST_API_KEY=
KAKAO_NATIVE_APP_KEY=
KAKAO_CLIENT_SECRET=         # (옵션) 보안 강화 시
KAKAO_REDIRECT_URI=https://api.petfinect/v1/auth/kakao/callback
```

### 검증 명령
```bash
# 토큰 교환 호환성 검증 (authCode를 미리 발급 받아)
curl -X POST 'https://kauth.kakao.com/oauth/token' \
  -d 'grant_type=authorization_code' \
  -d "client_id=$KAKAO_REST_API_KEY" \
  -d "redirect_uri=$KAKAO_REDIRECT_URI" \
  -d "code=$AUTH_CODE"
```

### 모바일 측 통합
- React Native: `@react-native-seoul/kakao-login` 또는 Expo `expo-auth-session`(WebBrowser 흐름).
- 카카오맵: `react-native-kakao-maps` 또는 WebView fallback.
- 시드 단계에서 두 옵션 모두 spike, 빠른 쪽 채택.

---

## 3. 공공데이터포털 (동물병원)

**리소스**: 농림축산식품부 또는 행정안전부 동물병원/수의사업 인허가 데이터.

### 절차
1. data.go.kr 회원가입.
2. "동물병원" 또는 "수의사업" 키워드로 데이터셋 검색.
   - 후보: "농림축산식품부\_동물병원 정보", "LOCALDATA 수의업".
3. 활용 신청 → 승인(보통 자동 또는 수시간).
4. 인증키 발급 → `.env`에 `DATA_GO_KR_API_KEY` 저장.
5. `infra/etl/hospital_sync.py`의 `fetch_page()`에 endpoint 채워넣고 일일 cron 등록.

### 환경변수
```
DATA_GO_KR_API_KEY=
```

### 데이터 모델 매핑
- 응답 → `Hospital(id, name, lat, lng, public_data_id, hours, services[])`
- 좌표 없는 데이터는 카카오 로컬 검색 API로 지오코딩 후 보강.

---

## 4. FatSecret (영양)

### 절차
1. FatSecret Platform 개발자 계정 가입.
2. 앱 등록 → Consumer Key/Secret 발급.
3. `foods.search`, `food.get` API 우선 검증.
4. **반려견 사료 데이터 빈약 가능성 확인** — 부족하면 자체 사료 DB 200건 시딩으로 보강.

### 자체 사료 DB 시딩 계획 (백업)
- 국내 인기 사료 50종 + 간식 30종 + 처방식 20종 + 일반식품 100종.
- 출처: 각 브랜드 공식 영양성분표 (출처 명시).
- 위치: `apps/api/seed/dog_foods.json` → `Food(name, brand, kcal_per_100g, protein, fat, ...)`.

### 환경변수
```
FATSECRET_CLIENT_ID=
FATSECRET_CLIENT_SECRET=
```

---

## 5. 오픈뱅킹 / 적금 ❌ MVP 제외

**결정**: 오픈뱅킹센터 등록은 사업자 등록이 필요하고 심사 기간이 김 → MVP 일정 무리.

### MVP 대안
- **외부 가입 딥링크**: 카카오페이/토스/은행 적금 상품 페이지로 연결 (광고성 표기 필요).
- **PoC mock 가입**: 인앱에서 가짜 계약 ID 발급 → 시연 영상에서 활용. 디스클레이머 명시.
- 본선 통과 후 (6.5 이후) 오픈뱅킹 정식 신청.

### 후보 적금 상품 조사 To-Do (PM)
- [ ] KB·신한·우리·하나 펫적금 상품 비교
- [ ] 카카오뱅크/토스뱅크 자유적금
- [ ] 펫보험사 제휴 상품 (메리츠·삼성화재·롯데손보)

---

## 6. 환경변수 종합 체크리스트

`.env.example`을 기준으로 5월 1주차 안에 모두 채워넣어야 함.

```
# Kakao
KAKAO_REST_API_KEY=          # 카카오 디벨로퍼 콘솔
KAKAO_NATIVE_APP_KEY=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=

# Caretail
CARETAIL_CLIENT_ID=          # 케어테일 파트너십 메일 응답 후
CARETAIL_CLIENT_SECRET=
CARETAIL_BASE_URL=

# 공공데이터
DATA_GO_KR_API_KEY=

# FatSecret
FATSECRET_CLIENT_ID=
FATSECRET_CLIENT_SECRET=

# 푸시
EXPO_ACCESS_TOKEN=

# Sentry (옵션)
SENTRY_DSN=
```

---

## 7. 통합 우선순위 점검 미팅

- **5.3 (W1 종료 직전)**: 5개 통합 상태 점검. 막힌 항목은 바로 fallback 결정.
- **5.10 (W2 중간)**: 케어테일 응답 받았는지 / mock provider 운용 여부 결정.
- **5.17 (W3 중간)**: 모든 통합 코드 freeze, E2E 검증.

---

## 8. 비상 fallback 매트릭스

| 통합 | Plan A | Plan B | Plan C |
|---|---|---|---|
| 케어테일 | 공식 API | mock provider + 시연 데이터 | (없음, 필수) |
| 카카오 로그인 | RN bridge | Expo auth-session WebBrowser | 이메일+비번(임시) |
| 카카오맵 | RN 네이티브 SDK | WebView 카카오맵 | OpenStreetMap+Leaflet |
| 공공데이터 | data.go.kr API | LOCALDATA CSV 다운로드 후 정적 시드 | — |
| FatSecret | 공식 API | 자체 사료 DB | 수동 입력만 |
| 오픈뱅킹 | (보류) | 외부 가입 링크 | mock 가입 PoC |
