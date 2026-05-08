package com.petfinect.api.openapi;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * Phase 9 — {@code /v3/api-docs} JSON 을 디스크로 내보내는 export 테스트.
 *
 * <h3>실행 방식</h3>
 * <ul>
 *   <li>기본은 {@link EnabledIfSystemProperty} 로 비활성. 일반 {@code ./gradlew test} 에선 skip.</li>
 *   <li>{@code ./gradlew exportOpenApi} 가 {@code -DpetfinectExportOpenApi=true} 시스템 프로퍼티와
 *       함께 이 테스트만 실행 → 산출 경로 {@code docs/api/openapi-w3-v2-java.json}.</li>
 * </ul>
 *
 * <h3>출력 정렬</h3>
 * <ul>
 *   <li>{@code SORT_PROPERTIES_ALPHABETICALLY} + {@code ORDER_MAP_ENTRIES_BY_KEYS} 로
 *       diff 가 매번 흔들리지 않게 한다 (springdoc 기본은 입력 순서).</li>
 *   <li>줄바꿈은 LF 강제 (CR 혼입 시 다른 OS 에서 깨짐 방지).</li>
 * </ul>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
@ActiveProfiles("test")
@EnabledIfSystemProperty(named = "petfinectExportOpenApi", matches = "true")
class OpenApiExportIT {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	).withDatabaseName("petfinect_test").withUsername("petfinect").withPassword("petfinect");

	@Autowired
	TestRestTemplate http;

	@Test
	void exportOpenApiSpecToDocsApi() throws Exception {
		ResponseEntity<String> resp = http.getForEntity("/v3/api-docs", String.class);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		String body = resp.getBody();
		assertThat(body).isNotBlank();

		ObjectMapper mapper = new ObjectMapper();
		JsonNode parsed = mapper.readTree(body);
		assertThat(parsed.path("openapi").asText()).startsWith("3.");
		assertThat(parsed.path("info").path("title").asText()).isEqualTo("PetFinect API");
		assertThat(parsed.path("paths").has("/v1/auth/kakao")).isTrue();
		assertThat(parsed.path("paths").has("/v1/hospitals/nearby")).isTrue();
		assertThat(parsed.path("paths").has("/v1/diagnose/image")).isTrue();

		// 서버 URL 의 랜덤 포트 (RANDOM_PORT 테스트 환경) 를 제거 → diff 안정화.
		// 실제 모바일 client 는 EXPO_PUBLIC_API_BASE 환경변수로 base URL 주입하므로
		// OpenAPI servers 항목은 codegen 결과에 영향 없음.
		if (parsed instanceof ObjectNode root) {
			root.remove("servers");
		}

		ObjectMapper writer = new ObjectMapper()
			.configure(SerializationFeature.INDENT_OUTPUT, true)
			.configure(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS, true);
		String pretty = writer.writeValueAsString(parsed);

		Path target = resolveTarget();
		Files.createDirectories(target.getParent());
		Files.writeString(
			target,
			pretty + System.lineSeparator(),
			StandardOpenOption.CREATE,
			StandardOpenOption.TRUNCATE_EXISTING
		);

		assertThat(Files.size(target)).isPositive();
		System.out.println("[openapi-export] wrote " + target.toAbsolutePath());
	}

	/**
	 * 모노레포 루트의 {@code docs/api/openapi-w3-v2-java.json}.
	 * Gradle 테스트 작업의 기본 작업 디렉터리는 {@code apps/api-java}.
	 */
	private static Path resolveTarget() {
		String override = System.getProperty("petfinectOpenApiOut");
		if (override != null && !override.isBlank()) {
			return Path.of(override).toAbsolutePath().normalize();
		}
		return Path.of("..", "..", "docs", "api", "openapi-w3-v2-java.json")
			.toAbsolutePath().normalize();
	}
}
