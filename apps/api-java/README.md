# PetFinect API · Spring Boot

Java/Spring 학습 + 마이그레이션 트랙. 단계별 진행은
[`.omc/plans/migration-cloud-api-to-spring-boot.md`](../../.omc/plans/migration-cloud-api-to-spring-boot.md)
참조.

## Stack

- Java 21 (toolchain — Gradle 가 자동 다운로드, foojay-resolver-convention)
- Spring Boot 4.0.6, Spring MVC, Spring Data JPA, Spring Security, Validation, Actuator
- PostgreSQL 16 + PostGIS 3.4 (Hibernate Spatial)
- Flyway (DB migration)
- JJWT 0.12 (HS256)
- springdoc-openapi 2.6 (OpenAPI export → shared-types codegen)
- Testcontainers (PostgreSQL/PostGIS 통합 테스트)

## Run

### 빌드/테스트

```bash
./gradlew test         # 단위 + 슬라이스 테스트
./gradlew bootRun      # 8001 포트 부팅 (Phase 1+ 부터 DB 필요)
./gradlew build        # jar 산출
```

### 헬스체크 (Phase 0)

```bash
./gradlew bootRun &
curl http://localhost:8001/healthz   # → {"status":"ok"}
```

> Phase 0 에서는 `application.yml` 의 datasource 가 dev DB (`jdbc:postgresql://localhost:5434/petfinect`) 를
> 가리키지만, Phase 1 에서 별도 DB(`petfinect_java`) 또는 Flyway baseline-on-migrate 정책 결정 후 활성화.

## Phase 진행

| Phase | 산출 | 상태 |
|---|---|---|
| 0 | scaffold + healthz + JDK21 toolchain | ✅ in progress |
| 1 | Flyway V1~V4 (Alembic 0001~0004 transcribe) | ⏳ |
| 2 | 13 JPA Entity + Repository | ⏳ |
| 3 | JWT + Kakao OAuth + Family RBAC | ⏳ |
| 4 | Family/Pet routes | ⏳ |
| 5 | Hospital nearby (Hibernate Spatial) | ⏳ |
| 6 | Storage abstraction + uploads | ✅ |
| 7 | AI server client (HMAC + mTLS) | ✅ |
| 8 | Diagnose orchestration | ⏳ |
| 9 | OpenAPI export → shared-types regen | ⏳ |
| 10 | 회귀 + 모바일 동작 검증 | ⏳ |
| 11 | Python apps/api deprecation | ⏳ |

## 호환성 계약

`apps/api` (FastAPI) 와 동일한 OpenAPI 계약을 유지. shared-types codegen 의 `paths` 가 변경되면
mobile typecheck 즉시 실패하므로 회귀 자동 검출.

## 디렉터리

```
src/main/java/com/petfinect/api/
  PetfinectApiApplication.java       Spring Boot entry
  config/                            Security/JPA/OpenAPI 설정
  domain/                            JPA Entity (Phase 2)
  repository/                        JpaRepository (Phase 2)
  service/                           비즈니스 로직 (Phase 3+)
  web/                               @RestController (Phase 3+)
  security/                          JWT, Kakao, RBAC (Phase 3)
  integration/                       외부 어댑터 (Phase 6+)
src/main/resources/
  application.yml                    개발 프로필
  application-test.yml               테스트 프로필 (Testcontainers)
  db/migration/                      Flyway V1__init.sql 등 (Phase 1)
src/test/java/com/petfinect/api/
  PetfinectApiApplicationTests.java  Phase 0 슬라이스 (HealthController)
```
