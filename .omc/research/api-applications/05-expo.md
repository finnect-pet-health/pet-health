# 05. Expo — 푸시 알림 (Push Notifications)

| 항목       | 내용                     |
|-----------|--------------------------|
| 우선순위   | **Low** (알림 기능)      |
| 담당자     | (채울 것)                |
| 현재 상태  | 신청 안 함               |

---

## 상태 이력

- [ ] 신청 안 함
- [ ] expo.dev 계정 생성 (날짜: )
- [ ] Access Token 발급 (날짜: )
- [ ] 실 디바이스 토큰 등록 (날짜: )

---

## 계정 정보

| 항목              | 값                                        |
|------------------|-------------------------------------------|
| Expo 계정 이메일  | (등록 시 사용한 이메일)                    |
| 계정 ID / slug    | -                                         |
| Access Token      | `.env` → `EXPO_ACCESS_TOKEN`              |
| 프로젝트 슬러그   | `petfinect` (expo.dev 프로젝트명)          |

---

## 신청 일자

> 미입력 — 발급 후 채울 것

---

## 신청 채널

- URL: https://expo.dev/
- 방법:
  1. expo.dev 계정 생성 (GitHub 또는 이메일)
  2. Account Settings → Access Tokens → "Create Token"
  3. 토큰 이름: `petfinect-push`
  4. 생성된 토큰 복사 → `.env` 입력

---

## 신청 시 첨부 자료

- 별도 첨부 불필요 (계정 생성 후 즉시 토큰 발급)

---

## 응답 예상 시간

**즉시** — 계정 생성 및 토큰 발급 모두 즉시

---

## 아키텍처 참고

### Access Token vs 디바이스 푸시 토큰

두 가지 토큰을 구분해야 함:

| 토큰 종류           | 발급 시점               | 용도                              |
|--------------------|------------------------|----------------------------------|
| **Access Token**   | expo.dev에서 즉시 발급  | 서버에서 Expo API 호출 인증       |
| **디바이스 토큰**  | 모바일 앱 설치 + 권한 허용 시 | 특정 디바이스로 푸시 전송         |

```typescript
// 모바일 앱에서 디바이스 토큰 등록 (Expo SDK)
import * as Notifications from 'expo-notifications';

const token = await Notifications.getExpoPushTokenAsync({
  projectId: 'your-expo-project-id',
});
// token.data → "ExponentPushToken[xxxx]" 형태로 서버에 저장
```

```python
# 서버에서 푸시 발송 (Access Token 사용)
import httpx

headers = {"Authorization": f"Bearer {os.getenv('EXPO_ACCESS_TOKEN')}"}
payload = {
    "to": device_push_token,  # 디바이스 토큰 (DB에서 조회)
    "title": "약 복용 시간",
    "body": "오후 3시 약 복용 알림입니다.",
}
httpx.post("https://exp.host/--/api/v2/push/send", json=payload, headers=headers)
```

---

## Fallback 계획

- 푸시 알림은 W2 내 발급 예정 (W1 블로커 아님)
- 미발급 시: 앱 내 인앱 알림 (배지/배너) 으로 대체 시연 가능
- 실 디바이스 토큰은 모바일 앱 빌드 후 등록 — 개발 단계에서 Expo Go 앱으로 테스트

---

## 다음 액션 (오늘 — 2026-05-07)

> **W2 안에 발급 예정 — 오늘 블로커 아님.**
> 여유 시 expo.dev 계정만 생성해두면 됨 (5분 소요).
> 디바이스 토큰은 모바일 앱 구현 후 자동 발급.
