package com.petfinect.api.web;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

/**
 * 통합 테스트 — Phase 3 인증 흐름 end-to-end.
 *
 * <h3>실행 흐름</h3>
 * <ol>
 *   <li>POST /v1/auth/kakao with mock-user-1 → 신규 사용자 + access/refresh 발급</li>
 *   <li>GET /v1/me without token → 401</li>
 *   <li>GET /v1/me with token → 200 + user info</li>
 *   <li>POST /v1/auth/refresh → 새 토큰 페어, 옛 refresh 폐기</li>
 *   <li>POST /v1/auth/logout → 204, 멱등</li>
 * </ol>
 *
 * <h3>{@link TestRestTemplate} vs RestClient</h3>
 * <ul>
 *   <li>{@code TestRestTemplate} 은 4xx/5xx 에 예외 안 던짐 → 상태 코드 직접 검증 편함.</li>
 *   <li>운영 코드에선 {@code RestClient} 사용. 통합 테스트에서만 RestTemplate 변종.</li>
 * </ul>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
@ActiveProfiles("test")
class AuthFlowIT {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	).withDatabaseName("petfinect_test").withUsername("petfinect").withPassword("petfinect");

	@Autowired
	TestRestTemplate http;

	@Test
	@SuppressWarnings("unchecked")
	void kakaoLogin_then_me_then_refresh_then_logout() {
		// 1) Kakao 로그인 — 토큰 발급
		ResponseEntity<Map> loginResp = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("auth_code", "mock-user-1", "redirect_uri", "http://localhost/cb"),
			Map.class
		);
		assertThat(loginResp.getStatusCode().value()).isEqualTo(200);
		Map<String, Object> login = loginResp.getBody();
		assertThat(login).isNotNull();
		String access = (String) login.get("access");
		String refresh = (String) login.get("refresh");
		assertThat(access).isNotBlank();
		assertThat(refresh).isNotBlank();
		Map<String, Object> userOut = (Map<String, Object>) login.get("user");
		assertThat(userOut).containsEntry("name", "테스트유저1");

		// 2) /me without token → 401
		ResponseEntity<String> meNoToken = http.getForEntity("/v1/me", String.class);
		assertThat(meNoToken.getStatusCode().value()).isEqualTo(401);

		// 3) /me with valid token → 200
		HttpHeaders authHeaders = new HttpHeaders();
		authHeaders.set(HttpHeaders.AUTHORIZATION, "Bearer " + access);
		ResponseEntity<Map> meResp = http.exchange(
			"/v1/me",
			HttpMethod.GET,
			new HttpEntity<>(authHeaders),
			Map.class
		);
		assertThat(meResp.getStatusCode().value()).isEqualTo(200);
		assertThat(meResp.getBody()).containsEntry("name", "테스트유저1");
		assertThat(meResp.getBody()).containsKey("families");

		// 4) Refresh — 새 페어 + 옛 refresh 무효화
		ResponseEntity<Map> refreshedResp = http.postForEntity(
			"/v1/auth/refresh",
			Map.of("refresh", refresh),
			Map.class
		);
		assertThat(refreshedResp.getStatusCode().value()).isEqualTo(200);
		String newRefresh = (String) refreshedResp.getBody().get("refresh");
		assertThat(newRefresh).isNotEqualTo(refresh);

		// 5) 옛 refresh 재사용 시도 → 401
		ResponseEntity<String> reusedResp = http.postForEntity(
			"/v1/auth/refresh",
			Map.of("refresh", refresh),
			String.class
		);
		assertThat(reusedResp.getStatusCode().value()).isEqualTo(401);

		// 6) Logout → 204, 멱등
		ResponseEntity<Void> logoutResp = http.postForEntity(
			"/v1/auth/logout",
			Map.of("refresh", newRefresh),
			Void.class
		);
		assertThat(logoutResp.getStatusCode().value()).isEqualTo(204);
	}

	@Test
	void kakaoLogin_invalidCode_returns400() {
		ResponseEntity<String> resp = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("auth_code", "garbage", "redirect_uri", "http://localhost/cb"),
			String.class
		);

		assertThat(resp.getStatusCode().value()).isEqualTo(400);
		assertThat(resp.getBody()).contains("INVALID_CODE");
	}

	@Test
	void me_withInvalidToken_returns401() {
		HttpHeaders headers = new HttpHeaders();
		headers.set(HttpHeaders.AUTHORIZATION, "Bearer not-a-valid-jwt");
		ResponseEntity<String> resp = http.exchange(
			"/v1/me",
			HttpMethod.GET,
			new HttpEntity<>(headers),
			String.class
		);

		assertThat(resp.getStatusCode().value()).isEqualTo(401);
	}

	@Test
	void kakaoLogin_validation_emptyCode_returns400() {
		ResponseEntity<String> resp = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("auth_code", "", "redirect_uri", "http://localhost"),
			String.class
		);

		assertThat(resp.getStatusCode().value()).isEqualTo(400);
		assertThat(resp.getBody()).contains("VALIDATION_FAILED");
	}

	@Test
	@SuppressWarnings("unchecked")
	void kakaoLogin_sameUser_returnsSameId_idempotent() {
		// 두 번째 호출 → 같은 사용자 (kakao_id 로 upsert)
		ResponseEntity<Map> first = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("auth_code", "mock-user-99", "redirect_uri", "http://localhost"),
			Map.class
		);
		ResponseEntity<Map> second = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("auth_code", "mock-user-99", "redirect_uri", "http://localhost"),
			Map.class
		);

		Map<String, Object> u1 = (Map<String, Object>) first.getBody().get("user");
		Map<String, Object> u2 = (Map<String, Object>) second.getBody().get("user");
		assertThat(u1.get("id")).isEqualTo(u2.get("id"));
	}
}
