plugins {
	java
	id("org.springframework.boot") version "4.0.6"
	id("io.spring.dependency-management") version "1.1.7"
}

group = "com.petfinect"
version = "0.0.1-SNAPSHOT"

java {
	toolchain {
		languageVersion = JavaLanguageVersion.of(21)
	}
}

repositories {
	mavenCentral()
}

dependencies {
	// Spring Boot starters
	implementation("org.springframework.boot:spring-boot-starter-actuator")
	implementation("org.springframework.boot:spring-boot-starter-data-jpa")
	implementation("org.springframework.boot:spring-boot-starter-flyway")
	implementation("org.springframework.boot:spring-boot-starter-security")
	implementation("org.springframework.boot:spring-boot-starter-validation")
	implementation("org.springframework.boot:spring-boot-starter-webmvc")

	// PostgreSQL + PostGIS
	runtimeOnly("org.postgresql:postgresql")
	implementation("org.flywaydb:flyway-database-postgresql")
	implementation("org.hibernate.orm:hibernate-spatial")  // PostGIS Geometry/Point 매핑

	// JWT (HS256, 동일 클레임 schema)
	implementation("io.jsonwebtoken:jjwt-api:0.12.6")
	runtimeOnly("io.jsonwebtoken:jjwt-impl:0.12.6")
	runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.12.6")

	// Lombok — boilerplate (getter/setter/builder/equals/hashCode) 제거. 학습용 의도 명료성 +
	// 엔티티 코드 30~50% 감축.
	compileOnly("org.projectlombok:lombok:1.18.34")
	annotationProcessor("org.projectlombok:lombok:1.18.34")
	testCompileOnly("org.projectlombok:lombok:1.18.34")
	testAnnotationProcessor("org.projectlombok:lombok:1.18.34")

	// OpenAPI export — shared-types codegen 의 source.
	// 3.x 가 Spring Framework 7 / Spring Boot 4 호환. 2.x 는 Spring 6 까지.
	implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:3.0.3")

	// Tests
	testImplementation("org.springframework.boot:spring-boot-starter-actuator-test")
	testImplementation("org.springframework.boot:spring-boot-starter-data-jpa-test")
	testImplementation("org.springframework.boot:spring-boot-starter-flyway-test")
	testImplementation("org.springframework.boot:spring-boot-starter-security-test")
	testImplementation("org.springframework.boot:spring-boot-starter-validation-test")
	testImplementation("org.springframework.boot:spring-boot-starter-webmvc-test")
	testImplementation("org.springframework.boot:spring-boot-testcontainers")
	// Spring Boot 4: TestRestTemplate + RestTemplateBuilder 가 별도 모듈로 분리
	testImplementation("org.springframework.boot:spring-boot-resttestclient")
	testImplementation("org.springframework.boot:spring-boot-restclient")
	testImplementation("org.testcontainers:junit-jupiter:1.20.4")
	testImplementation("org.testcontainers:postgresql:1.20.4")
	testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.withType<Test> {
	useJUnitPlatform()
}

// Phase 9 — OpenAPI export.
//
// `./gradlew exportOpenApi` 는 OpenApiExportIT 만 골라 실행하고,
// 시스템 프로퍼티 `petfinectExportOpenApi=true` 로 @EnabledIfSystemProperty 게이트를 푼다.
// 결과: <repo>/docs/api/openapi-w3-v2-java.json
//
// `--rerun` 으로 입력 캐시 무시 (springdoc 출력은 코드 변경에만 의존하지 않으므로
// JPA 메타/엔티티 어노테이션 추가 후에도 강제 재실행 필요).
tasks.register<Test>("exportOpenApi") {
	description = "Boot Spring (Testcontainers PostGIS) and export OpenAPI 3 to docs/api/openapi-w3-v2-java.json"
	group = "documentation"
	useJUnitPlatform()
	testClassesDirs = sourceSets["test"].output.classesDirs
	classpath = sourceSets["test"].runtimeClasspath
	systemProperty("petfinectExportOpenApi", "true")
	filter {
		includeTestsMatching("com.petfinect.api.openapi.OpenApiExportIT")
	}
	outputs.upToDateWhen { false }
}
