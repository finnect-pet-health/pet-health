# Spike · KakaoMap React Native (Expo) 통합 결정 문서

> 작성일: 2026-05-03 (W1 Day 2)
> 작성자: document-specialist agent
> 상위 plan: `.omc/plans/w1-auth-foundation.md` AC11
> 상태: **결정 완료** — W1은 옵션 B(WebView fallback) 우선, 옵션 A(native SDK)는 W2 재시도

---

## 1. 목적

이 spike는 **세 가지 질문에 대한 결정**을 내리기 위해 작성되었다.

1. `@react-native-kakao/map` (네이티브 브릿지) 이 Expo SDK 51 환경에서 `expo prebuild` + EAS Build 로 정상 빌드되는가?
2. 빌드가 가능하더라도 카카오 키 미발급 상태인 W1(~5.7) 기간 동안 시연 가능한 대안이 있는가?
3. 병원 매칭 spec 04(가까운 동물병원 3곳 표시) 시나리오를 W1 시연 수준으로 충족하는 최소 옵션은 무엇인가?

**결론 요약**: W1·W2 초반은 **옵션 B(WebView + 카카오 JS API)** 로 진행하고, 카카오 네이티브 키 발급 + EAS Build 환경이 갖춰진 W2 중반 이후 옵션 A 재시도를 권장한다.

---

## 2. 옵션 비교 표

| 옵션 | 장점 | 단점 | Expo 호환 | 추천 단계 |
|---|---|---|---|---|
| **A. `@react-native-kakao/map`** (네이티브 SDK) | 네이티브 성능, 오프라인 타일 캐시 가능, 폴리라인·GPS 추적 완전 지원 | expo prebuild 필수 (Expo Go 불가), EAS Build 설정 필요, 네이티브 키 필수, iOS Podfile/Android maven 추가 설정, 초기 설정 복잡도 높음 | 공식 지원 (`first-class Expo support` 명시), config plugin 제공 — 단 **development build** 필수 | W2 중반 이후 (키 발급 + EAS 환경 준비 후) |
| **B. WebView + 카카오 JS API** | 키 발급 즉시 적용, expo-webview 만으로 구현, Expo Go 동작, 빠른 prototype, JS 키(도메인 미검증 localhost 허용 가능) | 네이티브 대비 성능 낮음, 오프라인 불가, RN↔WebView 메시지 채널 구현 필요, GPS 권한 핸들오버 별도 처리 | 완전 호환 (`react-native-webview` Expo 공식 지원) | **W1·W2 초반 (현재 권장)** |
| **C. `react-native-maps` (Google Maps)** | 풍부한 문서·커뮤니티, Expo SDK 51 공식 지원 (`expo install react-native-maps`) | 카카오맵이 아닌 구글 지도 — 한국 심사위원 / 심사 기준 "카카오 생태계 통합" 에 불리, Google Maps API 별도 과금, 카카오 POI 데이터 미지원 | Expo 공식 지원, 단 iOS Google Maps 사용 시 SDK 55+ 에서 호환 이슈 있음 ([expo#43288](https://github.com/expo/expo/issues/43288)) | 카카오 생태계 연동이 불필요한 경우에만 고려 |

### 라이브러리 현황 요약 (2026-05 기준)

| 라이브러리 | npm 패키지 | GitHub Stars | 최신 릴리스 | Expo 공식 지원 | 유지보수 |
|---|---|---|---|---|---|
| `@react-native-kakao/map` | `@react-native-kakao/map` | 137 ★ (mym0404/react-native-kakao 전체) | v2.4.5 (2026-03-14) | 공식 명시 | 활성 |
| `react-native-kakao-maps` | `@jiggag/react-native-kakao-maps` | 20 ★ | 0.0.12 (2023-12-22) | 미명시 | **비활성** (2년+ 미업데이트) |
| `kakaomap_webview` | — (Flutter 전용) | 9 ★ | — | Flutter 전용 | 참고 불가 |

> [추정] `@react-native-kakao/map` v2.4.5 는 React Native 0.74 / Expo SDK 51 과 호환될 가능성이 높다. 공식 문서(rnkakao.mjstudio.net)에서 New Architecture + Expo 지원을 명시한다. 단 실제 빌드 검증 전까지는 추정 상태다.

---

## 3. Expo Prebuild 절차 (옵션 A)

> 이 섹션은 W2 중반 이후 옵션 A를 시도할 때 참조한다. W1 기간에는 실행하지 않는다.

### 3.1 사전 조건

- 카카오 디벨로퍼에서 **네이티브 앱 키** 발급 완료
- EAS CLI 설치: `npm install -g eas-cli`
- `eas login` 으로 Expo 계정 인증

### 3.2 패키지 설치

```bash
# apps/mobile 디렉터리에서
npx expo install @react-native-kakao/core @react-native-kakao/map expo-build-properties
```

### 3.3 app.json 플러그인 설정

```jsonc
// apps/mobile/app.json  (plugins 배열에 추가)
{
  "expo": {
    "plugins": [
      [
        "expo-build-properties",
        {
          "android": {
            "extraMavenRepos": [
              "https://devrepo.kakao.com/nexus/content/groups/public/"
            ]
          }
        }
      ],
      [
        "@react-native-kakao/core",
        {
          "nativeAppKey": "{{KAKAO_NATIVE_APP_KEY}}",
          "android": {},
          "ios": {}
        }
      ]
    ]
  }
}
```

> [추정] `nativeAppKey` 값을 하드코딩하는 대신, EAS Build secret 또는 `app.config.js` 에서 `process.env.EXPO_PUBLIC_KAKAO_NATIVE_APP_KEY` 로 동적 주입하는 방식을 권장한다. `app.json` 은 정적 파일이므로 환경변수 치환이 불가능하다.

#### app.config.js 동적 주입 패턴 (권장)

```js
// apps/mobile/app.config.js
import appJson from './app.json';

export default {
  ...appJson.expo,
  plugins: [
    ...(appJson.expo.plugins || []),
    [
      "@react-native-kakao/core",
      {
        nativeAppKey: process.env.EXPO_PUBLIC_KAKAO_NATIVE_APP_KEY,
        android: {},
        ios: {}
      }
    ]
  ]
};
```

### 3.4 iOS URL Scheme 설정

카카오 SDK는 `kakao{NATIVE_APP_KEY}://oauth` URL Scheme 을 Info.plist 에 등록해야 한다. `@react-native-kakao/core` 의 config plugin 이 prebuild 시 자동 추가한다. 수동으로 추가할 경우:

```xml
<!-- ios/{AppName}/Info.plist -->
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>kakao{{NATIVE_APP_KEY}}</string>
    </array>
  </dict>
</array>
```

**충돌 여부**: `expo-linking` 이 등록하는 `petfinect://` 스킴과 충돌하지 않는다. 스킴 이름이 다르므로 병존 가능하다.

### 3.5 prebuild 실행

```bash
# 기존 네이티브 디렉터리를 완전히 재생성
npx expo prebuild --clean --platform all

# 빌드 확인 (로컬)
npx expo run:ios    # Xcode 설치 필요
npx expo run:android
```

> [추정] `--clean` 없이 prebuild 를 실행하면 기존 Podfile/build.gradle 과 충돌이 발생할 수 있다. 첫 시도 시 `--clean` 필수.

### 3.6 EAS Build 사용

로컬 Xcode 없이 클라우드 빌드:

```bash
# eas.json 초기화
eas build:configure

# iOS development build
eas build --profile development --platform ios

# Android development build
eas build --profile development --platform android
```

`eas.json` 에 환경변수 주입:

```jsonc
// eas.json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "env": {
        "EXPO_PUBLIC_KAKAO_NATIVE_APP_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

> [추정] EAS Build 무료 티어는 월 30 빌드 제한이 있다. W2 기간에는 빌드 횟수를 아껴서 사용해야 한다.

---

## 4. WebView Fallback 시안 (옵션 B)

### 4.1 아키텍처 개요

```
[React Native 앱]
  └─ <WebView source={{ html: mapHtml }} />
       └─ [Kakao JS API 지도]
            └─ 마커 클릭 → window.ReactNativeWebView.postMessage(JSON)
  └─ onMessage → RN 상태 업데이트 → 병원 상세 화면으로 navigate
```

### 4.2 JS 키 주입 방식

JS API 키(`EXPO_PUBLIC_KAKAO_JS_KEY`)를 HTML 템플릿에 주입한다.

```tsx
// apps/mobile/src/components/KakaoMapWebView.tsx
import React from 'react';
import { WebView } from 'react-native-webview';
import Constants from 'expo-constants';

const JS_KEY = Constants.expoConfig?.extra?.kakaoJsKey
  ?? process.env.EXPO_PUBLIC_KAKAO_JS_KEY
  ?? '';

interface Hospital {
  id: string;
  name: string;
  lat: number;
  lng: number;
  address: string;
  distance: string;
}

interface Props {
  hospitals: Hospital[];
  userLat: number;
  userLng: number;
  onHospitalSelect: (hospital: Hospital) => void;
}

export function KakaoMapWebView({ hospitals, userLat, userLng, onHospitalSelect }: Props) {
  const markersJson = JSON.stringify(hospitals);

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    #map { width: 100vw; height: 100vh; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script type="text/javascript"
    src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=${JS_KEY}&autoload=false">
  </script>
  <script>
    kakao.maps.load(function() {
      var container = document.getElementById('map');
      var options = {
        center: new kakao.maps.LatLng(${userLat}, ${userLng}),
        level: 4
      };
      var map = new kakao.maps.Map(container, options);

      // 사용자 현재 위치 마커
      var userMarker = new kakao.maps.Marker({
        position: new kakao.maps.LatLng(${userLat}, ${userLng}),
        map: map
      });

      // 병원 마커
      var hospitals = ${markersJson};
      hospitals.forEach(function(h) {
        var marker = new kakao.maps.Marker({
          position: new kakao.maps.LatLng(h.lat, h.lng),
          map: map
        });
        kakao.maps.event.addListener(marker, 'click', function() {
          window.ReactNativeWebView.postMessage(JSON.stringify({
            type: 'HOSPITAL_SELECTED',
            payload: h
          }));
        });
      });
    });
  </script>
</body>
</html>`;

  function handleMessage(event: { nativeEvent: { data: string } }) {
    try {
      const msg = JSON.parse(event.nativeEvent.data);
      if (msg.type === 'HOSPITAL_SELECTED') {
        onHospitalSelect(msg.payload);
      }
    } catch {
      // ignore malformed messages
    }
  }

  return (
    <WebView
      source={{ html }}
      onMessage={handleMessage}
      javaScriptEnabled
      domStorageEnabled
      style={{ flex: 1 }}
    />
  );
}
```

### 4.3 GPS 권한 핸들오버 패턴

WebView 내부에서 `navigator.geolocation` 을 호출해도 Android WebView 에서는 권한이 거부될 수 있다. **RN 레이어에서 `expo-location` 으로 좌표를 획득하고 WebView 에 전달**하는 패턴을 사용한다.

```tsx
import * as Location from 'expo-location';

// 화면 마운트 시
const [status] = await Location.requestForegroundPermissionsAsync();
if (status !== 'granted') { /* 에러 처리 */ return; }
const loc = await Location.getCurrentPositionAsync({});
// → KakaoMapWebView 의 userLat, userLng prop 으로 전달
```

### 4.4 카카오 JS API 도메인 등록

JS API 는 등록된 도메인에서만 동작한다. WebView 의 `source={{ html }}` 인라인 HTML 방식은 도메인이 없으므로 **도메인 검증을 우회**할 수 없다.

해결책 2가지:
1. **`localhost` 등록**: 카카오 디벨로퍼 → 앱 → 플랫폼 → Web → `http://localhost` 추가. 인라인 HTML은 origin이 `null`이 되어 실패할 수 있음 — 이 경우 방법 2 사용.
2. **URI 방식**: WebView `source={{ uri: 'http://localhost:3000/map' }}` 로 로컬 HTTP 서버(또는 내장 번들)를 가리키고, 도메인을 `localhost` 로 등록. 단 Expo에서 로컬 HTTP 서버를 내장하려면 추가 작업 필요.
3. **개발 단계 임시**: `autoload=false` 방식으로 `kakao.maps.load()` 콜백을 사용하면 일부 환경에서 도메인 검증 없이 동작한다는 커뮤니티 사례가 있다. — [추정] 운영 환경에서는 보장되지 않음.

> W1 시연 목적으로는 `localhost` 도메인 등록 + `autoload=false` 패턴을 먼저 시도한다.

### 4.5 한계

| 항목 | 제한 |
|---|---|
| 오프라인 | JS API 는 온라인 전용. 타일 캐시 없음 |
| 성능 | WebView 렌더링 오버헤드. 100개 이상 마커에서 느려질 수 있음 |
| 한국 외 지역 | 카카오맵은 한국 중심 POI. 해외 사용 시 빈 지도 |
| GPS 권한 | WebView 자체 위치 권한 우회 필요 (expo-location 대신 사용) |
| 딥링크 | `kakao{KEY}://` 스킴은 JS API 에서 불필요. 카카오 네비게이션 앱 연동 시 별도 처리 필요 |

---

## 5. PetFinect 사용 시나리오 매핑

### 5.1 시나리오 1: 가까운 동물병원 3곳 표시 (병원 매칭 spec 04)

**필요 기능**: 마커, 사용자 현재 위치, 마커 클릭 → 병원 상세 화면

| 기능 | 옵션 A (Native) | 옵션 B (WebView) | W1 가능 여부 |
|---|---|---|---|
| 지도 표시 | `<KakaoMapView />` 컴포넌트 | WebView + HTML | B: 가능 |
| 사용자 위치 마커 | SDK 내장 | expo-location → postMessage inject | B: 가능 |
| 병원 마커 (3개) | Marker API | kakao.maps.Marker | B: 가능 |
| 마커 클릭 → 상세 | onMarkerPress 콜백 | postMessage → onMessage | B: 가능 |
| 거리 표시 | SDK 좌표 계산 | Haversine 공식 또는 카카오 로컬 API | B: 가능 |

**W1 데이터 소스**: 공공데이터포털 동물병원 API (별도 spike — external-apis.md 참조). 키 미발급 시 하드코딩 mock 데이터(3개 병원 좌표) 사용.

### 5.2 시나리오 2: 산책 경로 기록 (Phase 2)

**필요 기능**: Polyline 실시간 업데이트, GPS 지속 추적, 배경 실행

| 기능 | 옵션 A (Native) | 옵션 B (WebView) | 비고 |
|---|---|---|---|
| Polyline | SDK 내장 고성능 | kakao.maps.Polyline (JS) | B도 기술적으로 가능, 성능 한계 있음 |
| GPS 지속 추적 | expo-location background | expo-location → WebView inject | B: 실시간 업데이트 시 postMessage 빈도 높아 성능 저하 우려 |
| 배경 실행 | expo-task-manager 연계 | WebView 백그라운드 불가 | **B 불가** — Phase 2는 옵션 A 필수 |

> Phase 2(산책 경로 기록)는 옵션 A 없이는 구현이 어렵다. W2 중반까지 옵션 A 전환이 완료되어야 한다.

### 5.3 W1 시연 대상 시나리오

W1(~5.7) 시연에서는 **시나리오 1만 구현**한다. 옵션 B(WebView) 로 mock 병원 데이터 3개를 지도에 표시하고, 마커 클릭 시 병원 상세 화면으로 이동하는 흐름을 시연한다.

---

## 6. 권장 결정 (Day 3 시점, 2026-05-03)

### 6.1 W1 권장: 옵션 B 우선 진행

```
[지금 ~ W2 중반]   옵션 B (WebView + JS API)
[W2 중반 이후]     옵션 A (Native SDK) 재시도 및 전환
```

**근거**:
1. 카카오 네이티브 키 미발급 상태 — 옵션 A는 키 없이 빌드만 가능하고 지도 렌더링 불가능. W1 시연 목표 달성 불가.
2. `react-native-webview` 는 Expo SDK 51 공식 지원 패키지이므로 prebuild 없이 Expo Go + development build 모두에서 즉시 동작한다. 빠른 prototype에 유리.
3. W1 목표(병원 3곳 마커 표시 + 클릭 핸드오프)는 WebView 로 충분히 달성 가능하다.

### 6.2 옵션 A 전환 조건 (트리거)

다음 조건이 **모두** 충족되면 옵션 A로 전환한다:

| 조건 | 확인 방법 |
|---|---|
| 카카오 네이티브 앱 키 발급 완료 | 카카오 디벨로퍼 콘솔 확인 |
| EAS Build 계정 설정 완료 | `eas whoami` 성공 |
| `npx expo prebuild --clean` 성공 (에러 없음) | 터미널 출력 확인 |
| EAS Build iOS/Android development build 성공 | EAS 대시보드 빌드 상태 |

### 6.3 옵션 B 유지 조건 (포기 조건)

다음 중 하나라도 해당되면 W2 시점에도 옵션 B 유지:

- Day 4(5.5)까지 EAS Build 가 iOS 에서 연속 2회 이상 실패
- `@react-native-kakao/map` v2.4.5 와 React Native 0.74 간 호환 에러 미해결
- W2 종료(~5.14) 전까지 시연 일정이 촉박한 경우

---

## 7. 위험 & 대응

| 위험 | 가능성 | 영향 | 대응 |
|---|---|---|---|
| iOS native module 빌드 에러 (Expo SDK 51) | 중간 | 높음 | EAS Build 사용; 로컬 Xcode 불필요. `expo-build-properties` 로 Podfile 변경 최소화 |
| 카카오 JS API 도메인 검증 실패 (인라인 HTML) | 높음 | 중간 | `localhost` 도메인 등록; `autoload=false` 패턴 병행 시도 |
| WebView GPS 권한 미승인 (Android) | 높음 | 중간 | `expo-location` 으로 RN 레이어에서 좌표 획득 후 HTML inject |
| Expo Go 에서 native module 미동작 | 확정 (설계상) | 낮음 (예상된 제약) | development build 사용 (EAS 또는 `npx expo run:ios`). W1 시연은 Expo Go 가능한 옵션 B 사용 |
| 카카오맵 한국어 외 지원 약함 | 확정 | 낮음 (한국 시연) | PetFinect는 한국 출품작. 시연 환경 한국 한정 → 위험 없음 |
| `@react-native-kakao/map` 마이너 패키지 (137 stars) | 낮음 | 높음 | Phase 2 이전에 유지보수 상태 재확인. 대안: 직접 네이티브 모듈 래핑 |
| 공공데이터 동물병원 API 키 미발급 시 병원 데이터 없음 | 중간 | 중간 | W1 시연용 mock 병원 3개 하드코딩 (서울 강남 좌표 기준) |

---

## 8. Day 3 시점 결론 (2026-05-03)

### 8.1 현 시점 권장

**옵션 B(WebView + 카카오 JS API) 우선 진행, 옵션 A는 W2 중반 검증 예약.**

- `react-native-webview` 를 즉시 설치: `npx expo install react-native-webview`
- JS 키는 카카오 디벨로퍼에서 앱 등록 즉시 발급 가능 (네이티브 키와 별개)
- W1 시연 목표(병원 마커 3개 + 클릭 핸드오프)를 Day 5~6 에 구현 가능

### 8.2 카카오 키 발급 후 즉시 검증할 5개 항목

| # | 검증 항목 | 담당 | 예상 소요 |
|---|---|---|---|
| 1 | JS 키로 인라인 HTML 지도 렌더링 확인 (localhost 도메인 등록 후) | 모바일 | 30분 |
| 2 | `expo-location` 좌표 → WebView postMessage inject → 지도 중심 이동 | 모바일 | 1시간 |
| 3 | mock 병원 마커 3개 표시 + 클릭 → RN onMessage 수신 확인 | 모바일 | 1시간 |
| 4 | `npx expo prebuild --clean` 에러 없이 완료 (옵션 A 사전 검증) | 모바일 | 30분 |
| 5 | EAS Build development build 1회 성공 (iOS 또는 Android) | 모바일 + 인프라 | 2~3시간 |

### 8.3 W1 시연(5.7)에서 실제 동작할 옵션

| 시연 항목 | 구현 방식 | 데이터 |
|---|---|---|
| 지도 화면 표시 | 옵션 B (WebView) | 카카오 JS 타일 |
| 사용자 현재 위치 | expo-location → HTML inject | 실기기 GPS |
| 동물병원 마커 3개 | kakao.maps.Marker | mock 데이터 (하드코딩) |
| 마커 클릭 → 병원 상세 | postMessage → expo-router navigate | mock 병원 객체 |

> [추정] 카카오 JS 키가 5.4(Day 3~4) 이전에 발급되면 W1 시연에서 실제 카카오맵 타일을 사용할 수 있다. 발급이 늦어지면 지도 타일 없이 위치 마커만 표시하는 placeholder 화면으로 시연한다.

---

## 참고 자료

| 출처 | URL | 용도 |
|---|---|---|
| react-native-kakao GitHub | https://github.com/mym0404/react-native-kakao | 옵션 A 라이브러리 공식 레포 |
| RN Kakao 공식 문서 | https://rnkakao.mjstudio.net/en/docs/install-expo | Expo 설치 가이드 (403으로 직접 접근 불가 — 브라우저에서 확인 필요) |
| 카카오맵 JS API 가이드 | https://apis.map.kakao.com/web/guide/ | WebView fallback JS API |
| react-native-webview 공식 | https://github.com/react-native-webview/react-native-webview | WebView 통신 패턴 |
| Expo Adopting Prebuild | https://docs.expo.dev/guides/adopting-prebuild/ | prebuild 절차 |
| Expo react-native-webview | https://docs.expo.dev/versions/latest/sdk/webview/ | Expo 공식 WebView 문서 |
| 카카오 데브톡 RN+WebView 쓰레드 | https://devtalk.kakao.com/t/reactnative-webview-kakaomap/120230 | 도메인 등록 이슈 사례 |

