# Migration · apps/api (FastAPI) → Spring Boot 3.x (Java 21)

> 작성일: 2026-05-07
> 동기: 팀원의 Java/Spring 학습 목적
> 전략: **하이브리드** — cloud API 만 Java 로, AI 서버/ETL/모바일/shared-types 는 Python·TS 그대로

---

## 1. Goal

`apps/api` (FastAPI + SQLAlchemy + Alembic) 의 비즈니스 로직과 외부 인터페이스를 모두
**Spring Boot 3.3 + JPA + Flyway + JJWT** 기반의 새 모듈 `apps/api-java` 로 이식한다.
포팅 완료 후 동일 OpenAPI 계약을 만족하면 Python 모듈을 deprecate.

## 2. Out of Scope

- `apps/ai-server` (Python, torch + transformers) — 그대로
- `infra/etl/*` (Python, pyproj + asyncpg) — 그대로. Java 와는 DB 만 공유
- `apps/mobile` (Expo/RN TS) — API 계약 동일 유지 가정 → 코드 변경 없음
- `packages/shared-types` (TS) — Java 백엔드의 `springdoc-openapi` 출력으로 그대로 codegen
- PostgreSQL 16 + PostGIS 3.4 인프라 — 그대로 (DB 는 언어 무관)

---

## 3. Target Stack

```yaml
language:        Java 21 (LTS)
build:           Gradle 8 (Kotlin DSL)   # 또는 Maven — 팀원 선호 시 변경
framework:       Spring Boot 3.3
web:             Spring MVC (WebFlux 도 가능하나 학습 곡선상 MVC 추천)
data:            Spring Data JPA (Hibernate 6) + Hibernate Spatial (PostGIS)
migration:       Flyway 10
auth:            Spring Security 6 + JJWT 0.12 (HS256)
HTTP client:     Spring 6 RestClient (또는 WebClient) — AI 서버 mTLS+HMAC 호출용
test:            JUnit 5 + AssertJ + Spring Boot Test + Testcontainers (postgis/postgis:16-3.4)
docs:            springdoc-openapi-starter-webmvc-ui 2.x   # /v3/api-docs JSON 자동 export
runtime:         eclipse-temurin:21-jdk (build), eclipse-temurin:21-jre (run)
```

대안 (학습 노출용으로 선택지):
- **Kotlin** — Spring Boot 같은 JVM, 더 간결. 팀원이 Java 자체를 학습한다면 보류.
- **Maven** — XML 익숙하면 선호 가능. Gradle Kotlin DSL 이 monorepo 정합 더 좋음.

---

## 4. Directory Layout

```
apps/
  api/          (현행 FastAPI — Phase 11 까지 공존, 그 후 deprecated)
  api-java/     (신규)
    build.gradle.kts
    settings.gradle.kts
    Dockerfile
    src/
      main/
        java/com/petfinect/api/
          PetfinectApiApplication.java
          config/{SecurityConfig, OpenApiConfig, JpaConfig}.java
          domain/                     # JPA Entity (1:1 with current SQLAlchemy 모델)
          repository/                 # JpaRepository 인터페이스
          service/                    # 비즈니스 로직
          web/                        # @RestController + DTO
          security/                   # JWT, Kakao OAuth, RBAC
          integration/                # Kakao/Storage/AIServer/FatSecret 어댑터
        resources/
          application.yml
          application-test.yml
          db/migration/V1__init.sql, V2__w2_models.sql, V3__hospital_postgis.sql, V4__diagnosis_event.sql
      test/
        java/com/petfinect/api/
          web/...IntegrationTest.java
          repository/...Test.java
```

---

## 5. Phase 별 진행

### Phase 0 — Scaffold + dev env  (≈ 0.5d)
- `apps/api-java/build.gradle.kts` (deps: Spring Web, Data JPA, Security, Validation, Flyway, postgresql, hibernate-spatial, jjwt, springdoc, testcontainers)
- `apps/api-java/settings.gradle.kts`
- `apps/api-java/src/main/resources/application.yml` (dev) + `application-test.yml`
- `apps/api-java/Dockerfile` (multi-stage build)
- `docker-compose.yml` 의 `api` 서비스에 옵션 profile (`api-java`) 추가 (또는 별도 entry)
- `PetfinectApiApplication.java` 부트스트랩 + `/healthz` 라우트 1개 동작 확인

### Phase 1 — Flyway 마이그레이션 (≈ 0.5d)
- 4 Alembic 마이그를 SQL DDL 로 transcribe:
  - `V1__init.sql`     ← 0001_init.py (user/family/family_member/pet)
  - `V2__w2_models.sql` ← 0002_w2_models.py (meal/calendar_task/vet_visit/pet_food/notification_log/device + 6 enums)
  - `V3__hospital_postgis.sql` ← 0003_hospital_postgis.py (CREATE EXTENSION + hospital + GiST)
  - `V4__diagnosis_event.sql` ← 0004_diagnosis_event.py (diagnosis_event + 2 enums)
- Testcontainers PostGIS 컨테이너에서 `flywayMigrate` 통과 확인
- Python apps/api 테스트 DB 와 동일 schema 보장 (실 검증: `pg_dump --schema-only` diff)

### Phase 2 — Entities + Repositories (≈ 1d)
- 13 JPA `@Entity`:
  - User, Family, FamilyMember(@IdClass composite), Pet(species/conditions JSONB), Meal, CalendarTask, VetVisit, PetFood, NotificationLog, Device, Hospital(@Column(columnDefinition = "geometry(Point,4326)")), DiagnosisEvent
- `@Repository extends JpaRepository<...>` 13개
- @Converter for JSONB (Map/List → String) — Hibernate 6 native JSON support 활용
- `@Test` repo CRUD smoke (Testcontainers)

### Phase 3 — Auth: JWT + Kakao OAuth + RBAC (≈ 1d)
- `JwtTokenProvider` (HS256, 15min access / 14d refresh) — Python `python-jose` 와 동일 클레임
- `SecurityConfig` (Bearer filter, /v1/auth/* permitAll, 그 외 authenticated)
- `KakaoOAuthClient` interface + `RealKakaoOAuthClient` (RestClient) + `MockKakaoOAuthClient` (`@Profile("dev|test")`)
- `@PreAuthorize` 또는 custom `RoleAccessExpression` 으로 가족 RBAC 구현
- 라우트: POST /v1/auth/kakao, /refresh, /logout. GET /v1/me

### Phase 4 — Family/Pet routes + RBAC (≈ 1d)
- /v1/families CRUD + invite code 발급/조회/조인
- /v1/families/{family_id}/pets nested
- /v1/pets/{pet_id} (RBAC: 가족 멤버만)
- 통합 테스트 (RestAssured 또는 MockMvc) — Python tests 동일 케이스 1:1 포팅

### Phase 5 — Hospital nearby (Hibernate Spatial) (≈ 0.5d)
- `Hospital` 엔티티에 `Point location` (org.locationtech.jts)
- `HospitalRepository.findNearby(double lat, lng, int radiusM, int limit)` — JPQL `function('ST_DWithin', ...)`
- /v1/hospitals/nearby — distance ASC + specialty 파라미터 (W3 무시, W4 활용 예정)

### Phase 6 — Storage abstraction + /v1/uploads/* (≈ 0.5d)
- `StorageProvider` interface (`presignPut`, `presignGet`, `fetchBytes`, `putBytes`)
- `InMemoryStorage` (ConcurrentHashMap, mock-s3:// URL)
- `S3StorageProvider` 자리 (W3-v2 D2 — AWS SDK v2)
- /v1/uploads/presign + /v1/uploads/raw (dev only — `@Profile("dev")` 가드)

### Phase 7 — AI 서버 클라이언트 (≈ 0.5d)
- `AIServerClient` interface
- `MockAIServerClient` (sha256 결정적 응답 — Python 동일 알고리즘)
- `RealAIServerClient` (RestClient + custom `SslContextFactory` + HMAC 헤더)
- HMAC: `hmac-sha256` shared_secret + raw bytes → hex digest

### Phase 8 — Diagnose orchestration (≈ 0.5d)
- /v1/diagnose/image, /v1/diagnose/audio
- /v1/pets/{pet_id}/diagnoses (created_at DESC, RBAC)
- DiagnosisEvent insert (pet_id FK CASCADE, modality/action enum)

### Phase 9 — OpenAPI export → shared-types codegen (≈ 0.5d)
- springdoc-openapi 로 자동 `/v3/api-docs` JSON 생성
- 기존 `packages/shared-types/scripts/generate.sh` 우선순위에 `docs/api/openapi-w3-v2-java.json` 추가
- 모바일 typecheck 통과 검증 (계약 변경 0 가설)

### Phase 10 — 회귀 + 모바일 동작 검증 (≈ 0.5d)
- docker-compose 로 Java backend + 기존 Postgres + AI server 동시 부팅
- 모바일 EXPO_PUBLIC_API_BASE 를 Java 백엔드 URL 로 swap
- Mock 사용자 로그인 → 진단 → 병원 nearby 흐름 수동 시연

### Phase 11 — Python apps/api deprecation (≈ 0.25d)
- `apps/api/README.md` 에 deprecation 헤드라인 추가
- CI workflow `.github/workflows/api.yml` 비활성화 또는 삭제
- 모노레포 README 업데이트

**총 추정**: 6.5 ~ 7 일 풀타임 (1인). 학습 목적이므로 1.5 ~ 2 주 yet learning pace 가정.

---

## 6. 호환성 계약

| 항목 | Python (현재) | Java (목표) | 변경? |
|---|---|---|---|
| HTTP API | `/v1/*` 25 라우트 | 동일 path/payload/status | ❌ |
| Error envelope | `{ "detail": { "error": { "code", "message" } } }` | 동일 | ❌ |
| JWT | HS256, sub=user_id, fids list, roles map | 동일 | ❌ |
| Auth header | `Authorization: Bearer {access}` | 동일 | ❌ |
| 좌표 시스템 | EPSG:4326 (WGS84) lat/lng | 동일 | ❌ |
| Mock S3 URL scheme | `mock-s3://{bucket}/{key}?op=put&...` | 동일 | ❌ |
| HMAC 헤더 | `X-AI-HMAC: hex(sha256(secret, body))` | 동일 | ❌ |
| Pagination | (현재 limit param) | 동일 | ❌ |

OpenAPI export 결과의 schema (TypeScript codegen) 가 호환되도록 DTO 명/필드명 1:1 일치 강제.

---

## 7. Verification

각 Phase EOD:
- `./gradlew test` 통과
- 통합 테스트 (Testcontainers PostGIS) 통과
- 핵심 엔드포인트 → Python 백엔드 응답과 byte-for-byte 일치 (jq normalize 후)

전체 마이그 완료 게이트:
1. `apps/api-java/src/test/**/*.java` 전부 green
2. `pnpm -C apps/mobile typecheck` 0 errors (Java OpenAPI 로 codegen 후)
3. 수동 시연: mock 로그인 → diagnose/image → /pets/{id}/diagnoses → /hospitals/nearby flow 동작
4. Python `apps/api` deprecation 마크

---

## 8. Risks

| # | 위험 | 대응 |
|---|---|---|
| R1 | Java/Spring 학습 곡선이 일정 초과 | Phase 단위로 PR 검토. Phase 1-3 까지 1주차에 끝나면 정상 페이스. 미달 시 4 인 분담 → 스플릿 |
| R2 | JSONB 매핑 (pet.conditions, diagnosis_event.top_results) 호환성 | Hibernate 6 의 `@JdbcTypeCode(SqlTypes.JSON)` 사용. 통합 테스트로 round-trip 검증 |
| R3 | PostGIS Hibernate Spatial JTS 의존성 충돌 | Spring Boot starter 버전 핀 + Testcontainers 부팅 시 검증 |
| R4 | Kakao OAuth 응답 schema 차이 (httpx vs RestClient) | mock 클라이언트 일관 + real 클라이언트는 동일 endpoint/payload 사용 |
| R5 | 두 백엔드 동시 운영 중 DB 락 경합 | dev/test DB 1개 공유 가정. CI 에서 별도 DB 사용 |
| R6 | shared-types codegen 의 nullable/optional 표기 차이 | OpenAPI 출력 비교 + 필요 시 `@Nullable` 명시 |

---

## 9. 첫 commit 단위 (Phase 0)

```
apps/api-java/build.gradle.kts                     [new]
apps/api-java/settings.gradle.kts                  [new]
apps/api-java/gradle.properties                    [new]
apps/api-java/.gitignore                           [new]
apps/api-java/Dockerfile                           [new]
apps/api-java/src/main/java/com/petfinect/api/PetfinectApiApplication.java         [new]
apps/api-java/src/main/java/com/petfinect/api/web/HealthController.java            [new]
apps/api-java/src/main/resources/application.yml                                   [new]
apps/api-java/src/main/resources/application-test.yml                              [new]
apps/api-java/src/test/java/com/petfinect/api/PetfinectApiApplicationTests.java    [new]
docker-compose.yml                                 [edit: api-java service profile]
README.md                                          [edit: Java backend 진입 가이드]
```

검증: `./gradlew bootRun` 으로 8001/healthz 응답 200, `./gradlew test` 1 case green.

---

## 10. Changelog

- 2026-05-07 — 초안 작성. 하이브리드 전략 (Java cloud API + Python AI/ETL/Mobile) + 11 Phase + 호환성 계약 + 6 risks.
