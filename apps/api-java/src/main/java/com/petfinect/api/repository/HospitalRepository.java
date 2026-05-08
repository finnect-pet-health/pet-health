package com.petfinect.api.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.Hospital;

/**
 * 가까운 동물병원 조회 — PostGIS {@code ST_DWithin} + 거리 ASC.
 *
 * <h3>Native SQL 사용 이유</h3>
 * <ul>
 *   <li>{@code ST_DWithin} / {@code ST_Distance} 가 JPQL 의 표준 함수로 정의되지 않음.</li>
 *   <li>JPQL {@code function('ST_DWithin', ...)} 도 가능하지만 가독성 ↓.
 *       Spring Data 에서 native SQL 이 학습 자료로 더 명료.</li>
 *   <li>{@code geography} 캐스트로 m 단위 정확한 거리 계산.</li>
 * </ul>
 */
@Repository
public interface HospitalRepository extends JpaRepository<Hospital, UUID> {

	Optional<Hospital> findByMgmtNo(String mgmtNo);

	@Query(
		value = """
			SELECT h.*,
				ST_Distance(
					h.location::geography,
					ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
				) AS distance_m
			FROM hospital h
			WHERE h.location IS NOT NULL
			  AND ST_DWithin(
				  h.location::geography,
				  ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
				  :radiusM
			  )
			ORDER BY distance_m ASC
			LIMIT :limit
			""",
		nativeQuery = true
	)
	List<Object[]> findNearbyRaw(
		@Param("lat") double lat,
		@Param("lng") double lng,
		@Param("radiusM") int radiusM,
		@Param("limit") int limit
	);

	/**
	 * /v1/hospitals/nearby 응답에 필요한 컬럼만 명시 select — Python 라우트 contract 와 1:1.
	 *
	 * <p>{@code Object[]} 컬럼 순서: id(UUID), mgmt_no(String), name(String),
	 * road_addr(String), tel(String), lat(double), lng(double), distance_m(double).
	 *
	 * <p>학습 포인트: native query 가 raw 컬럼을 던질 때 Spring Data 가 인터페이스 projection
	 * 으로 자동 매핑 가능 — 단순 record 매핑은 이 방식이 표준.
	 */
	@Query(
		value = """
			SELECT
				h.id AS id,
				h.mgmt_no AS mgmt_no,
				h.name AS name,
				h.road_addr AS road_addr,
				h.tel AS tel,
				ST_Y(h.location::geometry) AS lat,
				ST_X(h.location::geometry) AS lng,
				ST_Distance(
					h.location::geography,
					ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
				) AS distance_m
			FROM hospital h
			WHERE h.location IS NOT NULL
			  AND ST_DWithin(
				  h.location::geography,
				  ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
				  :radiusM
			  )
			ORDER BY distance_m ASC
			LIMIT :limit
			""",
		nativeQuery = true
	)
	List<NearbyProjection> findNearby(
		@Param("lat") double lat,
		@Param("lng") double lng,
		@Param("radiusM") int radiusM,
		@Param("limit") int limit
	);

	/**
	 * Spring Data JPA interface projection — getter 시그니처가 SELECT alias 와 일치하면
	 * 런타임 proxy 가 자동 생성. native query 결과를 record/DTO 로 빠르게 매핑.
	 */
	interface NearbyProjection {
		java.util.UUID getId();
		String getMgmtNo();
		String getName();
		String getRoadAddr();
		String getTel();
		double getLat();
		double getLng();
		double getDistanceM();
	}
}
