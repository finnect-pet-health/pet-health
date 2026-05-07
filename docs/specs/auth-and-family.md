# Spec · Auth & Family RBAC

> 카카오 OAuth + JWT + Family 그룹 권한 모델 상세 설계.
> 의존: `/home/hidi/.claude/plans/ai-compressed-codd.md` § 5, § 6

## 1. 목표

- 한국 사용자에게 마찰 없는 로그인 (카카오 단일 OAuth).
- 한 강아지를 **여러 가족 구성원이 공유**해서 케어할 수 있게.
- 권한 분리: **owner**(의료·결제 가능) / **member**(기록·일정 참여만).
- 비밀번호 저장 없음 (카카오만), Apple 계정은 Phase 2.

## 2. 인증 플로우 (카카오 OAuth)

```
[Mobile]                  [Cloud API]               [Kakao]
   │   1. login()             │                        │
   │ ───────────────────────▶ │                        │
   │   (in-app browser/SDK)   │                        │
   │ ────────────────────────────────────────────────▶ │
   │   2. authorize ─ user ─ approve                   │
   │ ◀──────────────────────────────────────────────── │
   │   3. authCode                                     │
   │ ───────────────────────▶ │                        │
   │   POST /auth/kakao       │ 4. exchange (server)   │
   │   {authCode}             │ ────────────────────▶  │
   │                          │ ◀────────────────────  │
   │                          │   kakao access_token   │
   │                          │ 5. /v2/user/me ───────▶│
   │                          │ ◀──────── kakao_user   │
   │                          │ 6. upsert User         │
   │                          │ 7. issue JWT pair      │
   │ ◀─────────────────────── │                        │
   │   {access, refresh}      │                        │
```

### 2.1 토큰 정책
- **Access token**: 15분, claims = `{sub: user_id, fids: [active_family_ids], roles: {fid: role}}`
- **Refresh token**: 14일, opaque, Redis에 `refresh:{user_id}:{jti}` 저장 (회전·폐기 용이).
- 회전 정책: refresh 사용 시 새 access + 새 refresh 발급, 직전 refresh 즉시 폐기.
- 로그아웃: 해당 jti의 Redis 키 삭제 → 모든 후속 거부.
- 키: HS256 (서버 단일 인스턴스 MVP) → Phase 2에 RS256 + JWKS.

### 2.2 카카오 비즈 앱 설정
- 동의 항목: 닉네임(필수), 카카오계정 이메일(선택), 프로필 이미지(선택).
- 리다이렉트 URI: `kakao{APP_KEY}://oauth` (모바일) + `https://api.petfinect/v1/auth/kakao/callback` (디버그).
- 환경변수: `KAKAO_REST_API_KEY`, `KAKAO_NATIVE_APP_KEY`, `KAKAO_CLIENT_SECRET`.

## 3. 도메인 모델 상세

```python
class User(Base):
    id: UUID                  # 내부 PK
    kakao_id: str             # 카카오 회원번호 (unique, indexed)
    email: str | None
    name: str
    profile_image: str | None
    created_at: datetime
    last_login_at: datetime

class Family(Base):
    id: UUID
    name: str                 # 예: "보리네"
    owner_id: UUID            # User.id (생성자, 소유권 이전 가능)
    invite_code: str          # 8자 base32, rotateable
    created_at: datetime

class FamilyMember(Base):
    family_id: UUID
    user_id: UUID
    role: Enum("owner", "member")
    joined_at: datetime
    PRIMARY KEY (family_id, user_id)
    INDEX (user_id)           # 내 가족 목록 조회

# Pet은 별도 spec이지만 Family와 1:N
class Pet(Base):
    id: UUID
    family_id: UUID           # 가족 단위 소속 (cascade delete X, soft archive)
    species: Enum             # 'dog' MVP
    ...
```

### 3.1 권한 매트릭스

| 액션 | guest | member | owner |
|---|---|---|---|
| Pet/Health/Meal 조회 | ❌ | ✅ | ✅ |
| Meal/CalendarTask 생성·완료 체크 | ❌ | ✅ | ✅ |
| Pet 프로필 수정 | ❌ | ❌ | ✅ |
| Pet 추가/삭제 | ❌ | ❌ | ✅ |
| 가족 멤버 초대·강퇴 | ❌ | ❌ | ✅ |
| 적금 가입·결제 | ❌ | ❌ | ✅ |
| 소유권 이전 | ❌ | ❌ | ✅ |

> Phase 2에서 `co-owner` 역할 추가 검토(보호자 부부 양쪽 결제권).

## 4. API 엔드포인트

### 4.1 Auth
```
POST /v1/auth/kakao
  body: { authCode: string, redirectUri: string }
  200:  { access: jwt, refresh: opaque, user: {id, name, profile_image} }
  4xx:  invalid_code, kakao_unreachable

POST /v1/auth/refresh
  body: { refresh: string }
  200:  { access, refresh }
  401:  expired / revoked

POST /v1/auth/logout
  header: Authorization
  body:   { refresh }
  204

GET  /v1/me
  header: Authorization
  200:  { id, name, profile_image, families: [{id, name, role}] }
```

### 4.2 Family
```
POST /v1/families
  body: { name }
  200:  { family: Family, member: { role: 'owner' } }

GET  /v1/families
  200: [{ id, name, role, member_count }]

POST /v1/families/{id}/invite
  body: { ttl_hours?: int = 72 }
  200:  { invite_code, expires_at }
  permission: owner

POST /v1/families/join
  body: { invite_code }
  200:  { family, role: 'member' }

GET  /v1/families/{id}/members
  200: [{ user_id, name, role, joined_at }]
  permission: member or owner

PATCH /v1/families/{id}/members/{user_id}
  body: { role: 'member'|'owner' }   # 소유권 이전
  permission: owner
  200

DELETE /v1/families/{id}/members/{user_id}
  permission: owner (또는 본인 탈퇴)
  204
```

### 4.3 에러 표준
```json
{ "error": { "code": "FORBIDDEN", "message": "owner only" } }
```
| code | http | 의미 |
|---|---|---|
| `UNAUTHORIZED` | 401 | 토큰 없음/만료/위조 |
| `FORBIDDEN` | 403 | 역할 부족 |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `INVITE_EXPIRED` | 410 | 초대 만료 |
| `RATE_LIMITED` | 429 | 초대/로그인 시도 과다 |

## 5. 권한 체크 미들웨어 (FastAPI)

```python
async def require_family(family_id: UUID, role: Literal["member","owner"] = "member"):
    """Depends 미들웨어. 토큰 → user_id → FamilyMember 검증."""
    user = current_user()
    membership = await db.fetch_one(
        "SELECT role FROM family_member WHERE family_id=:f AND user_id=:u",
        f=family_id, u=user.id,
    )
    if not membership:
        raise HTTPError(404, "NOT_FOUND")
    if role == "owner" and membership.role != "owner":
        raise HTTPError(403, "FORBIDDEN", "owner only")
    return membership
```

> Pet 단위 액션은 항상 `family_id = pet.family_id` 로딩 후 `require_family` 호출.

## 6. 초대 링크 UX

- 형태: `https://petfinect.app/i/{invite_code}` 또는 카카오톡 공유.
- 미가입자가 클릭 → 카카오 로그인 → 자동 join.
- 초대 코드 TTL 기본 72시간, owner가 회수 가능 (`POST /families/{id}/invite/revoke`).
- 1 family당 동시 활성 코드는 1개 (간단성).

## 7. 보안·프라이버시

- 카카오 access_token은 서버에 저장하지 않음 (인증 후 즉시 폐기). 추후 refresh 필요 기능(예: 카카오 친구 목록)이 생기면 별도 `KakaoToken` 테이블에 암호화 저장.
- 모든 PII는 Postgres + at-rest encryption(클라우드 KMS).
- 로그에는 `user_id` 외 PII 미기록.
- 개인정보 처리 방침: 카카오 닉네임·이메일·프로필 사진 + 펫 헬스 데이터(별도 동의 항목 운영).
- Family 탈퇴 시 본인 작성 데이터(Meal·CalendarTask)는 가족에 잔존(작성자만 익명화), Pet 자체는 owner 책임.

## 8. 테스트 체크리스트

- [ ] 카카오 mock 서버로 OAuth 콜백 happy path
- [ ] authCode 재사용 시 4xx
- [ ] refresh 회전 후 직전 토큰 사용 시 401
- [ ] owner만 invite 발급
- [ ] member가 owner 액션 시도 → 403
- [ ] 초대 만료 후 join → 410
- [ ] 같은 가족 중복 join 차단
- [ ] 마지막 owner 탈퇴 차단 (소유권 이전 강제)
- [ ] 동일 카카오 ID 재로그인 → 같은 User upsert

## 9. 마일스톤

| W | 산출 |
|---|---|
| W1 | 카카오 디벨로퍼 앱·키 발급, /auth/kakao 동작, JWT 발급/검증 |
| W2 | Family CRUD, 초대·가입, 미들웨어 결합, 단위 테스트 |
| W3 | 모바일 통합 + 권한 매트릭스 E2E |
| W4 | 보안 점검 + 시연 데이터 시드 |
