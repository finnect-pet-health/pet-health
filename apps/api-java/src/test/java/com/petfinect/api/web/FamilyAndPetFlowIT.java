package com.petfinect.api.web;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
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
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

/**
 * Phase 4 Family/Pet 흐름 통합 테스트.
 *
 * <h3>커버리지</h3>
 * <ol>
 *   <li>Owner: family 생성 → 펫 생성 → 자기 family 조회 OK</li>
 *   <li>Member: 초대 코드로 가입 → 멤버 목록/펫 목록 OK, 초대 발급 시도 → 403</li>
 *   <li>Outsider: 다른 family ID 접근 시도 → 404 (존재 누설 방지)</li>
 *   <li>RBAC token-DB 일관성: 새로 가입한 family 라도 DB 조회로 통과</li>
 * </ol>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
@ActiveProfiles("test")
class FamilyAndPetFlowIT {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	).withDatabaseName("petfinect_test").withUsername("petfinect").withPassword("petfinect");

	@Autowired
	TestRestTemplate http;

	@Test
	@SuppressWarnings("unchecked")
	void fullFlow_owner_invite_member_pet_rbac() {
		// === 1) Owner 로그인 ===
		String ownerAccess = login("mock-user-100");

		// === 2) Family 생성 ===
		ResponseEntity<Map> createResp = http.exchange(
			"/v1/families",
			HttpMethod.POST,
			authJson(ownerAccess, Map.of("name", "우리집")),
			Map.class
		);
		assertThat(createResp.getStatusCode().value()).isEqualTo(200);
		Map<String, Object> family = (Map<String, Object>) createResp.getBody().get("family");
		String familyId = (String) family.get("id");
		assertThat(family.get("name")).isEqualTo("우리집");
		assertThat(((Map<String, Object>) createResp.getBody().get("member")).get("role")).isEqualTo("owner");

		// owner 토큰엔 아직 이 family 가 없음 → 새 토큰 받아야 RBAC 빠른길 적용 (DB 조회로도 통과는 됨)
		String ownerAccess2 = login("mock-user-100"); // 새 토큰 (fids 갱신)

		// === 3) Pet 생성 (owner 만 허용) ===
		ResponseEntity<Map> petResp = http.exchange(
			"/v1/families/" + familyId + "/pets",
			HttpMethod.POST,
			authJson(ownerAccess2, Map.of(
				"breed", "포메라니안",
				"weight", 4.5,
				"neutered", true,
				"conditions", List.of("아토피")
			)),
			Map.class
		);
		assertThat(petResp.getStatusCode().value()).isEqualTo(200);
		String petId = (String) petResp.getBody().get("id");
		assertThat(petResp.getBody().get("breed")).isEqualTo("포메라니안");
		assertThat(petResp.getBody().get("species")).isEqualTo("dog");
		assertThat((List<String>) petResp.getBody().get("conditions")).contains("아토피");

		// === 4) 초대 코드 발급 ===
		ResponseEntity<Map> inviteResp = http.exchange(
			"/v1/families/" + familyId + "/invite",
			HttpMethod.POST,
			authJson(ownerAccess2, Map.of("ttlHours", 24)),
			Map.class
		);
		assertThat(inviteResp.getStatusCode().value()).isEqualTo(200);
		String inviteCode = (String) inviteResp.getBody().get("inviteCode");
		assertThat(inviteCode).hasSize(8);

		// === 5) Member 로그인 + 가입 ===
		String memberAccess = login("mock-user-200");

		ResponseEntity<Map> joinResp = http.exchange(
			"/v1/families/join",
			HttpMethod.POST,
			authJson(memberAccess, Map.of("inviteCode", inviteCode)),
			Map.class
		);
		assertThat(joinResp.getStatusCode().value()).isEqualTo(200);
		assertThat(joinResp.getBody().get("role")).isEqualTo("member");

		// === 6) Member: 펫 목록 조회 OK ===
		ResponseEntity<List> petsResp = http.exchange(
			"/v1/families/" + familyId + "/pets",
			HttpMethod.GET,
			authJson(memberAccess, null),
			List.class
		);
		assertThat(petsResp.getStatusCode().value()).isEqualTo(200);
		assertThat(petsResp.getBody()).hasSize(1);

		// === 7) Member: 펫 직접 조회 OK ===
		ResponseEntity<Map> petGetResp = http.exchange(
			"/v1/pets/" + petId,
			HttpMethod.GET,
			authJson(memberAccess, null),
			Map.class
		);
		assertThat(petGetResp.getStatusCode().value()).isEqualTo(200);

		// === 8) Member: 멤버 목록 조회 OK (이름 2명) ===
		ResponseEntity<List> membersResp = http.exchange(
			"/v1/families/" + familyId + "/members",
			HttpMethod.GET,
			authJson(memberAccess, null),
			List.class
		);
		assertThat(membersResp.getStatusCode().value()).isEqualTo(200);
		assertThat(membersResp.getBody()).hasSize(2);

		// === 9) Member: 초대 발급 시도 → 403 (owner 만 가능) ===
		ResponseEntity<String> inviteForbidden = http.exchange(
			"/v1/families/" + familyId + "/invite",
			HttpMethod.POST,
			authJson(memberAccess, Map.of("ttlHours", 24)),
			String.class
		);
		assertThat(inviteForbidden.getStatusCode().value()).isEqualTo(403);

		// === 10) Member: 펫 생성 시도 → 403 ===
		ResponseEntity<String> petForbidden = http.exchange(
			"/v1/families/" + familyId + "/pets",
			HttpMethod.POST,
			authJson(memberAccess, Map.of("breed", "리트리버", "neutered", false)),
			String.class
		);
		assertThat(petForbidden.getStatusCode().value()).isEqualTo(403);

		// === 11) Outsider: 자기 토큰으로 다른 family 접근 → 404 (존재 누설 방지) ===
		String outsiderAccess = login("mock-user-300");
		ResponseEntity<String> outsiderPets = http.exchange(
			"/v1/families/" + familyId + "/pets",
			HttpMethod.GET,
			authJson(outsiderAccess, null),
			String.class
		);
		assertThat(outsiderPets.getStatusCode().value()).isEqualTo(404);

		// === 12) Outsider: 펫 직접 조회 → 404 ===
		ResponseEntity<String> outsiderPet = http.exchange(
			"/v1/pets/" + petId,
			HttpMethod.GET,
			authJson(outsiderAccess, null),
			String.class
		);
		assertThat(outsiderPet.getStatusCode().value()).isEqualTo(404);
	}

	@Test
	void joinByCode_invalid_returns404() {
		String access = login("mock-user-400");
		ResponseEntity<String> resp = http.exchange(
			"/v1/families/join",
			HttpMethod.POST,
			authJson(access, Map.of("inviteCode", "NOSUCHC0")),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(404);
		assertThat(resp.getBody()).contains("NOT_FOUND");
	}

	@Test
	@SuppressWarnings("unchecked")
	void joinByCode_alreadyMember_returns409() {
		String access = login("mock-user-500");
		ResponseEntity<Map> created = http.exchange(
			"/v1/families",
			HttpMethod.POST,
			authJson(access, Map.of("name", "본가")),
			Map.class
		);
		String familyId = (String) ((Map<String, Object>) created.getBody().get("family")).get("id");

		ResponseEntity<Map> invite = http.exchange(
			"/v1/families/" + familyId + "/invite",
			HttpMethod.POST,
			authJson(access, Map.of("ttlHours", 24)),
			Map.class
		);
		String code = (String) invite.getBody().get("inviteCode");

		ResponseEntity<String> joinAgain = http.exchange(
			"/v1/families/join",
			HttpMethod.POST,
			authJson(access, Map.of("inviteCode", code)),
			String.class
		);
		assertThat(joinAgain.getStatusCode().value()).isEqualTo(409);
		assertThat(joinAgain.getBody()).contains("ALREADY_MEMBER");
	}

	@Test
	void families_endpoints_require_auth() {
		ResponseEntity<String> resp = http.getForEntity("/v1/families", String.class);
		assertThat(resp.getStatusCode().value()).isEqualTo(401);
	}

	@Test
	void getFamily_invalidUuidPath_returns404() {
		String access = login("mock-user-600");
		ResponseEntity<String> resp = http.exchange(
			"/v1/families/not-a-uuid/members",
			HttpMethod.GET,
			authJson(access, null),
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(404);
	}

	// === helpers ===

	@SuppressWarnings("unchecked")
	private String login(String mockCode) {
		ResponseEntity<Map> resp = http.postForEntity(
			"/v1/auth/kakao",
			Map.of("authCode", mockCode, "redirectUri", "http://localhost"),
			Map.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		return (String) resp.getBody().get("access");
	}

	private HttpEntity<Object> authJson(String access, Object body) {
		HttpHeaders h = new HttpHeaders();
		h.setBearerAuth(access);
		h.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
		return new HttpEntity<>(body, h);
	}
}
