package com.petfinect.api.web;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.resttestclient.autoconfigure.AutoConfigureTestRestTemplate;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

/**
 * Phase 5 — {@code GET /v1/hospitals/nearby} 통합 테스트.
 *
 * <h3>시드 전략</h3>
 * <ul>
 *   <li>{@link JdbcTemplate} 으로 4개 병원 직접 INSERT — JPA 우회 (PostGIS POINT 빌드 단순화).</li>
 *   <li>좌표는 서울시청 (37.5665, 126.9780) 인접 ~3.5km 범위로 분포.</li>
 *   <li>{@code ST_SetSRID(ST_MakePoint(lng, lat), 4326)} — 명시적 SRID 4326.</li>
 * </ul>
 *
 * <h3>인증 정책 검증</h3>
 * <ul>
 *   <li>permitAll 라우트 — Authorization 헤더 없이도 200 응답.</li>
 * </ul>
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestRestTemplate
@Testcontainers
@ActiveProfiles("test")
class HospitalNearbyIT {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	).withDatabaseName("petfinect_test").withUsername("petfinect").withPassword("petfinect");

	@Autowired
	TestRestTemplate http;

	@Autowired
	JdbcTemplate jdbc;

	@BeforeEach
	void seedHospitals() {
		jdbc.update("DELETE FROM hospital");
		// 서울시청 (37.5665, 126.9780) 기준
		insert("seoul-001", "동물병원A", "서울시 중구 1", "02-100-0001", 37.5665, 126.9780); // ~0m
		insert("seoul-002", "동물병원B", "서울시 종로구 2", "02-100-0002", 37.5700, 126.9800); // ~400m
		insert("seoul-003", "동물병원C", "서울시 마포구 3", "02-100-0003", 37.5500, 126.9500); // ~3km
		insert("busan-004", "부산병원D", "부산시 해운대 4", "051-200-0001", 35.1796, 129.0756); // ~325km
	}

	private void insert(String mgmtNo, String name, String addr, String tel, double lat, double lng) {
		UUID id = UUID.randomUUID();
		jdbc.update("""
			INSERT INTO hospital (id, mgmt_no, name, road_addr, lot_addr, zip, tel, status, authority_code, location)
			VALUES (?, ?, ?, ?, '', '', ?, '운영중', 'TEST',
				ST_SetSRID(ST_MakePoint(?, ?), 4326))
			""",
			id, mgmtNo, name, addr, tel, lng, lat
		);
	}

	@Test
	@SuppressWarnings("unchecked")
	void nearby_seoulCity_returns3InRange_distanceAsc() {
		ResponseEntity<List> resp = http.getForEntity(
			"/v1/hospitals/nearby?lat=37.5665&lng=126.9780&radius_m=5000&limit=10",
			List.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		List<Map<String, Object>> body = (List<Map<String, Object>>) resp.getBody();

		// 부산은 5km radius 안에 없으므로 3개만
		assertThat(body).hasSize(3);
		// 거리 ASC
		assertThat((String) body.get(0).get("mgmt_no")).isEqualTo("seoul-001");
		double d0 = ((Number) body.get(0).get("distance_m")).doubleValue();
		double d1 = ((Number) body.get(1).get("distance_m")).doubleValue();
		double d2 = ((Number) body.get(2).get("distance_m")).doubleValue();
		assertThat(d0).isLessThanOrEqualTo(d1);
		assertThat(d1).isLessThanOrEqualTo(d2);

		// 좌표 round-trip — POINT 에서 ST_X / ST_Y 로 추출
		double lat0 = ((Number) body.get(0).get("lat")).doubleValue();
		double lng0 = ((Number) body.get(0).get("lng")).doubleValue();
		assertThat(lat0).isCloseTo(37.5665, org.assertj.core.data.Offset.offset(1e-6));
		assertThat(lng0).isCloseTo(126.9780, org.assertj.core.data.Offset.offset(1e-6));
	}

	@Test
	@SuppressWarnings("unchecked")
	void nearby_smallRadius_filtersOut() {
		ResponseEntity<List> resp = http.getForEntity(
			"/v1/hospitals/nearby?lat=37.5665&lng=126.9780&radius_m=100&limit=10",
			List.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		// 100m radius 내에는 시청 자체 (0m) 만
		assertThat((List<?>) resp.getBody()).hasSize(1);
	}

	@Test
	@SuppressWarnings("unchecked")
	void nearby_limitParam_caps() {
		ResponseEntity<List> resp = http.getForEntity(
			"/v1/hospitals/nearby?lat=37.5665&lng=126.9780&radius_m=5000&limit=2",
			List.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		assertThat((List<?>) resp.getBody()).hasSize(2);
	}

	@Test
	void nearby_publicAccess_noAuthRequired() {
		// Authorization 헤더 없이도 200 — permitAll 라우트
		ResponseEntity<List> resp = http.getForEntity(
			"/v1/hospitals/nearby?lat=37.5665&lng=126.9780",
			List.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
	}

	@Test
	void nearby_invalidLat_returns400() {
		ResponseEntity<String> resp = http.getForEntity(
			"/v1/hospitals/nearby?lat=999&lng=126.9780",
			String.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(400);
	}

	@Test
	@SuppressWarnings("unchecked")
	void nearby_busanQuery_findsBusanHospital() {
		ResponseEntity<List> resp = http.getForEntity(
			"/v1/hospitals/nearby?lat=35.1796&lng=129.0756&radius_m=2000&limit=10",
			List.class
		);
		assertThat(resp.getStatusCode().value()).isEqualTo(200);
		List<Map<String, Object>> body = (List<Map<String, Object>>) resp.getBody();
		assertThat(body).hasSize(1);
		assertThat(body.get(0).get("mgmt_no")).isEqualTo("busan-004");
	}
}
