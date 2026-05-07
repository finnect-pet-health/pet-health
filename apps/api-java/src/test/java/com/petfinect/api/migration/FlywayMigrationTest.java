package com.petfinect.api.migration;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.ArrayList;
import java.util.List;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

/**
 * Phase 1 검증 — Flyway V1~V4 가 fresh PostGIS DB 에서 모두 적용되고
 * 13 테이블 + flyway_schema_history 가 생성되는지 확인.
 *
 * 학습 포인트:
 * - {@link Testcontainers}: 테스트 라이프사이클에 docker container 자동 부팅/종료
 * - {@link ServiceConnection}: Spring Boot 가 컨테이너 JDBC URL 을 자동 주입
 * - postgis/postgis 이미지: PostgreSQL + PostGIS 확장 사전 설치 (V3 migration 의존)
 */
@SpringBootTest
@ActiveProfiles("test")
@Testcontainers
class FlywayMigrationTest {

	@Container
	@ServiceConnection
	static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(
		// postgis/postgis 이미지는 Testcontainers 표준 postgres 와 동일 동작 — 명시적
		// 호환성 선언 필요. PostGIS 확장이 사전 설치된 채로 부팅 (V3 migration 의존).
		DockerImageName.parse("postgis/postgis:16-3.4").asCompatibleSubstituteFor("postgres")
	)
		.withDatabaseName("petfinect_test")
		.withUsername("petfinect")
		.withPassword("petfinect");

	@Autowired
	private DataSource dataSource;

	@Test
	void allFourMigrationsApplied_andTablesCreated() throws Exception {
		List<String> tables = new ArrayList<>();
		try (var conn = dataSource.getConnection();
			var rs = conn.getMetaData().getTables(null, "public", "%", new String[] {"TABLE"})) {
			while (rs.next()) {
				tables.add(rs.getString("TABLE_NAME"));
			}
		}

		// Alembic 13 테이블 + Flyway 1 메타 = 14
		assertThat(tables).contains(
			// V1
			"user", "family", "family_member", "pet",
			// V2
			"meal", "calendar_task", "vet_visit", "pet_food",
			"notification_log", "device",
			// V3
			"hospital",
			// V4
			"diagnosis_event",
			// Flyway 메타
			"flyway_schema_history"
		);
	}

	@Test
	void hospitalLocationIsPostgisPoint() throws Exception {
		try (var conn = dataSource.getConnection();
			var stmt = conn.createStatement();
			var rs = stmt.executeQuery(
				"SELECT type, srid FROM geometry_columns "
				+ "WHERE f_table_name = 'hospital' AND f_geometry_column = 'location'")) {
			assertThat(rs.next()).isTrue();
			assertThat(rs.getString("type")).isEqualTo("POINT");
			assertThat(rs.getInt("srid")).isEqualTo(4326);
		}
	}

	@Test
	void enumsCreated() throws Exception {
		List<String> enums = new ArrayList<>();
		try (var conn = dataSource.getConnection();
			var stmt = conn.createStatement();
			var rs = stmt.executeQuery(
				"SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname")) {
			while (rs.next()) {
				enums.add(rs.getString("typname"));
			}
		}
		assertThat(enums).contains(
			"member_role", "pet_species",
			"meal_source", "meal_food_kind",
			"calendar_task_kind", "pet_food_source",
			"notification_channel", "device_platform",
			"diagnosis_modality", "diagnosis_action"
		);
	}
}
