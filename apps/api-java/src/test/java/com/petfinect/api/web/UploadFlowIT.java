package com.petfinect.api.web;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

/**
 * Phase 6 — 업로드 흐름 통합 테스트.
 *
 * <h3>커버리지</h3>
 * <ol>
 *   <li>presign: image/jpeg → 200 + mock-s3 URL + key 패턴 검증</li>
 *   <li>presign: audio/wav → 200</li>
 *   <li>presign: 잘못된 content-type → 400 INVALID_CONTENT_TYPE</li>
 *   <li>presign: 인증 없이 → 401</li>
 *   <li>raw upload: 정상 → 200 + bytes 카운트 + 후속 fetch 가능</li>
 *   <li>raw upload: 빈 body → 400 EMPTY_BODY</li>
 *   <li>raw upload: 잘못된 content-type → 400</li>
 * </ol>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
@ActiveProfiles("test")
class UploadFlowIT {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	).withDatabaseName("petfinect_test").withUsername("petfinect").withPassword("petfinect");

	@Autowired
	TestRestTemplate http;

	@Test
	@SuppressWarnings("unchecked")
	void presign_image_returnsKeyAndUrl() {
		String access = login("mock-user-700");

		ResponseEntity<Map> resp = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "image", "contentType", "image/jpeg")),
			Map.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		Map<String, Object> body = resp.getBody();
		String key = (String) body.get("key");
		String url = (String) body.get("url");
		int ttl = ((Number) body.get("ttlS")).intValue();

		assertThat(key).matches("^uploads/image/[0-9a-f-]{36}/[0-9a-f-]{36}\\.jpg$");
		assertThat(url).startsWith("mock-s3://");
		assertThat(url).contains("op=put");
		assertThat(url).contains("ct=image/jpeg");
		assertThat(ttl).isEqualTo(600);
	}

	@Test
	@SuppressWarnings("unchecked")
	void presign_audio_wav() {
		String access = login("mock-user-701");

		ResponseEntity<Map> resp = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "audio", "contentType", "audio/wav")),
			Map.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		assertThat((String) resp.getBody().get("key")).endsWith(".wav");
	}

	@Test
	void presign_invalidContentType_returns400() {
		String access = login("mock-user-702");

		ResponseEntity<String> resp = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "image", "contentType", "application/pdf")),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(400);
		assertThat(resp.getBody()).contains("INVALID_CONTENT_TYPE");
	}

	@Test
	void presign_modalityMismatch_returns400() {
		String access = login("mock-user-703");

		// audio modality 인데 image content-type → 400
		ResponseEntity<String> resp = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "audio", "contentType", "image/jpeg")),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(400);
	}

	@Test
	void presign_noAuth_returns401() {
		HttpHeaders h = new HttpHeaders();
		h.setContentType(MediaType.APPLICATION_JSON);
		ResponseEntity<String> resp = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			new HttpEntity<>(Map.of("modality", "image", "contentType", "image/jpeg"), h),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(401);
	}

	@Test
	@SuppressWarnings("unchecked")
	void rawUpload_thenStored() {
		String access = login("mock-user-710");

		// 1) presign 으로 key 발급
		ResponseEntity<Map> presign = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "image", "contentType", "image/png")),
			Map.class
		);
		String key = (String) presign.getBody().get("key");

		// 2) raw 라우트로 bytes 직접 업로드
		byte[] payload = new byte[]{(byte) 0x89, 'P', 'N', 'G', 1, 2, 3, 4};
		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.IMAGE_PNG);

		ResponseEntity<Map> rawResp = http.exchange(
			"/v1/uploads/raw?key=" + key,
			HttpMethod.POST,
			new HttpEntity<>(payload, h),
			Map.class
		);
		assertThat(rawResp.getStatusCode().value()).isEqualTo(200);
		assertThat(rawResp.getBody().get("key")).isEqualTo(key);
		assertThat(((Number) rawResp.getBody().get("bytes")).intValue()).isEqualTo(payload.length);
	}

	@Test
	void rawUpload_emptyBody_returns400() {
		String access = login("mock-user-711");

		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.IMAGE_JPEG);

		ResponseEntity<String> resp = http.exchange(
			"/v1/uploads/raw?key=uploads/image/test/empty.jpg",
			HttpMethod.POST,
			new HttpEntity<>(new byte[0], h),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(400);
		assertThat(resp.getBody()).contains("EMPTY_BODY");
	}

	@Test
	void rawUpload_invalidContentType_returns400() {
		String access = login("mock-user-712");

		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.APPLICATION_PDF);

		ResponseEntity<String> resp = http.exchange(
			"/v1/uploads/raw?key=uploads/image/test/x.pdf",
			HttpMethod.POST,
			new HttpEntity<>(new byte[]{1, 2, 3}, h),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(400);
		assertThat(resp.getBody()).contains("INVALID_CONTENT_TYPE");
	}

	// === helpers ===

	@SuppressWarnings("unchecked")
	private String login(String mockCode) {
		ResponseEntity<Map> resp = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("authCode", mockCode, "redirectUri", "http://localhost"),
			Map.class
		);
		return (String) resp.getBody().get("access");
	}

	private HttpEntity<Object> authJson(String access, Object body) {
		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.APPLICATION_JSON);
		return new HttpEntity<>(body, h);
	}
}
