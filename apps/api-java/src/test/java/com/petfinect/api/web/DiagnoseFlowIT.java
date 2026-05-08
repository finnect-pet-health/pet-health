package com.petfinect.api.web;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;
import java.util.Set;

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
 * Phase 8 — 진단 흐름 통합 테스트.
 *
 * <h3>커버리지 (Python {@code apps/api/tests/test_diagnose.py} 와 1:1)</h3>
 * <ol>
 *   <li>image happy path — 200 + modality/s3Ref/topResults skin 라벨 검증</li>
 *   <li>audio happy path — 200 + 한국어 카테고리 셋</li>
 *   <li>list 정렬/limit — created_at DESC, limit=2 가 3건 중 최신 2건</li>
 *   <li>RBAC — 다른 가족 멤버가 펫 진단 이력 조회 시 404</li>
 *   <li>존재하지 않는 펫 → 404</li>
 *   <li>인증 누락 → 401</li>
 * </ol>
 *
 * <h3>설계 메모</h3>
 * <ul>
 *   <li>업로드는 {@code /v1/uploads/raw} 로 진행. dev profile 가드 안 걸리게 {@code test} 프로파일 사용.</li>
 *   <li>UploadService 가 production profile 에서만 raw 차단 → 여기선 활성.</li>
 *   <li>각 테스트 unique mock-user-NN, unique key — 테스트간 격리.</li>
 * </ul>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
@ActiveProfiles("test")
class DiagnoseFlowIT {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	).withDatabaseName("petfinect_test").withUsername("petfinect").withPassword("petfinect");

	@Autowired
	TestRestTemplate http;

	@Test
	@SuppressWarnings("unchecked")
	void diagnose_image_happy_path() {
		Ctx ctx = bootstrapOwnerWithPet("mock-user-800");
		String key = uploadImage(ctx.access, "fake-image-bytes-for-mock-ai".getBytes());

		ResponseEntity<Map> resp = http.exchange(
			"/v1/diagnose/image",
			HttpMethod.POST,
			authJson(ctx.access, Map.of("pet_id", ctx.petId, "image_s3_key", key, "region", "skin")),
			Map.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		Map<String, Object> body = resp.getBody();
		assertThat(body.get("modality")).isEqualTo("image");
		assertThat(body.get("s3_ref")).isEqualTo(key);
		assertThat(body.get("pet_id")).isEqualTo(ctx.petId);
		assertThat(body.get("action")).isIn("immediate", "schedule", "observe");
		double conf = ((Number) body.get("confidence_top1")).doubleValue();
		assertThat(conf).isBetween(0.0, 1.0);

		List<Map<String, Object>> top = (List<Map<String, Object>>) body.get("top_results");
		assertThat(top).hasSize(3);
		Set<String> labels = top.stream().map(m -> (String) m.get("label")).collect(java.util.stream.Collectors.toSet());
		assertThat(labels).containsAnyOf("skin_redness", "skin_normal", "skin_alopecia");
	}

	@Test
	@SuppressWarnings("unchecked")
	void diagnose_audio_happy_path() {
		Ctx ctx = bootstrapOwnerWithPet("mock-user-801");
		String key = uploadAudio(ctx.access, new byte[]{(byte) 0xff, (byte) 0xfb, 'a', 'u', 'd', 'i', 'o'});

		ResponseEntity<Map> resp = http.exchange(
			"/v1/diagnose/audio",
			HttpMethod.POST,
			authJson(ctx.access, Map.of("pet_id", ctx.petId, "audio_s3_key", key)),
			Map.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		Map<String, Object> body = resp.getBody();
		assertThat(body.get("modality")).isEqualTo("audio");
		assertThat(body.get("s3_ref")).isEqualTo(key);

		List<Map<String, Object>> top = (List<Map<String, Object>>) body.get("top_results");
		assertThat(top).hasSize(1);
		assertThat((String) top.get(0).get("category"))
			.isIn("정상", "기침", "이상호흡", "꼬르륵", "기타");
	}

	@Test
	@SuppressWarnings("unchecked")
	void diagnoses_list_orders_desc_with_limit() {
		Ctx ctx = bootstrapOwnerWithPet("mock-user-802");

		// 3건 적재 (서로 다른 bytes → 서로 다른 score, 서로 다른 created_at)
		for (int i = 0; i < 3; i++) {
			String key = uploadImage(ctx.access, ("img-bytes-" + i).getBytes());
			ResponseEntity<Map> resp = http.exchange(
				"/v1/diagnose/image",
				HttpMethod.POST,
				authJson(ctx.access, Map.of("pet_id", ctx.petId, "image_s3_key", key, "region", "eye")),
				Map.class
			);
			assertThat(resp.getStatusCode().value()).isEqualTo(200);
		}

		ResponseEntity<List> listResp = http.exchange(
			"/v1/pets/" + ctx.petId + "/diagnoses?limit=2",
			HttpMethod.GET,
			authJson(ctx.access, null),
			List.class
		);
		assertThat(listResp.getStatusCode().value()).isEqualTo(200);
		List<Map<String, Object>> rows = listResp.getBody();
		assertThat(rows).hasSize(2);
		// created_at DESC — 첫 행이 최신.
		String first = (String) rows.get(0).get("created_at");
		String second = (String) rows.get(1).get("created_at");
		assertThat(first.compareTo(second)).isGreaterThanOrEqualTo(0);
	}

	@Test
	void diagnoses_list_rbac_other_family_returns_404() {
		// owner 가 펫 + 진단 보유. 다른 가족 사용자 (B) 가 그 펫의 진단 이력 접근 → 404.
		Ctx owner = bootstrapOwnerWithPet("mock-user-803");
		String otherAccess = login("mock-user-804");

		ResponseEntity<String> resp = http.exchange(
			"/v1/pets/" + owner.petId + "/diagnoses",
			HttpMethod.GET,
			authJson(otherAccess, null),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(404);
		assertThat(resp.getBody()).contains("NOT_FOUND");
	}

	@Test
	void diagnose_image_unknown_pet_returns_404() {
		Ctx ctx = bootstrapOwnerWithPet("mock-user-805");
		String key = uploadImage(ctx.access, "x".getBytes());

		ResponseEntity<String> resp = http.exchange(
			"/v1/diagnose/image",
			HttpMethod.POST,
			authJson(ctx.access, Map.of(
				"pet_id", "11111111-2222-3333-4444-555555555555",
				"image_s3_key", key,
				"region", "skin"
			)),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(404);
	}

	@Test
	void diagnose_image_invalidUuidPath_returns_404() {
		Ctx ctx = bootstrapOwnerWithPet("mock-user-806");
		String key = uploadImage(ctx.access, "y".getBytes());

		ResponseEntity<String> resp = http.exchange(
			"/v1/diagnose/image",
			HttpMethod.POST,
			authJson(ctx.access, Map.of(
				"pet_id", "not-a-uuid",
				"image_s3_key", key,
				"region", "skin"
			)),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(404);
	}

	@Test
	void diagnose_requires_auth() {
		HttpHeaders h = new HttpHeaders();
		h.setContentType(MediaType.APPLICATION_JSON);
		ResponseEntity<String> resp = http.exchange(
			"/v1/diagnose/image",
			HttpMethod.POST,
			new HttpEntity<>(Map.of(
				"pet_id", "11111111-2222-3333-4444-555555555555",
				"image_s3_key", "x",
				"region", "skin"
			), h),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(401);
	}

	// === helpers ===

	private record Ctx(String access, String familyId, String petId) {}

	@SuppressWarnings("unchecked")
	private Ctx bootstrapOwnerWithPet(String mockCode) {
		String access = login(mockCode);

		ResponseEntity<Map> familyResp = http.exchange(
			"/v1/families",
			HttpMethod.POST,
			authJson(access, Map.of("name", "테스트가족-" + mockCode)),
			Map.class
		);
		assertThat(familyResp.getStatusCode().value()).isEqualTo(200);
		Map<String, Object> family = (Map<String, Object>) familyResp.getBody().get("family");
		String familyId = (String) family.get("id");

		// 새 token 으로 fids 갱신 — 펫 생성 시 owner 빠른길.
		String access2 = login(mockCode);

		ResponseEntity<Map> petResp = http.exchange(
			"/v1/families/" + familyId + "/pets",
			HttpMethod.POST,
			authJson(access2, Map.of("breed", "mixed", "neutered", false)),
			Map.class
		);
		assertThat(petResp.getStatusCode().value()).isEqualTo(200);
		String petId = (String) petResp.getBody().get("id");

		return new Ctx(access2, familyId, petId);
	}

	@SuppressWarnings("unchecked")
	private String login(String mockCode) {
		ResponseEntity<Map> resp = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("auth_code", mockCode, "redirect_uri", "http://localhost"),
			Map.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		return (String) resp.getBody().get("access");
	}

	@SuppressWarnings("unchecked")
	private String uploadImage(String access, byte[] bytes) {
		ResponseEntity<Map> presign = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "image", "content_type", "image/jpeg")),
			Map.class
		);
		assertThat(presign.getStatusCode().value()).isEqualTo(200);
		String key = (String) presign.getBody().get("key");

		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.IMAGE_JPEG);
		ResponseEntity<Map> raw = http.exchange(
			"/v1/uploads/raw?key=" + key,
			HttpMethod.POST,
			new HttpEntity<>(bytes, h),
			Map.class
		);
		assertThat(raw.getStatusCode().value()).isEqualTo(200);
		return key;
	}

	@SuppressWarnings("unchecked")
	private String uploadAudio(String access, byte[] bytes) {
		ResponseEntity<Map> presign = http.exchange(
			"/v1/uploads/presign",
			HttpMethod.POST,
			authJson(access, Map.of("modality", "audio", "content_type", "audio/wav")),
			Map.class
		);
		assertThat(presign.getStatusCode().value()).isEqualTo(200);
		String key = (String) presign.getBody().get("key");

		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.parseMediaType("audio/wav"));
		ResponseEntity<Map> raw = http.exchange(
			"/v1/uploads/raw?key=" + key,
			HttpMethod.POST,
			new HttpEntity<>(bytes, h),
			Map.class
		);
		assertThat(raw.getStatusCode().value()).isEqualTo(200);
		return key;
	}

	private HttpEntity<Object> authJson(String access, Object body) {
		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(MediaType.APPLICATION_JSON);
		return new HttpEntity<>(body, h);
	}
}
