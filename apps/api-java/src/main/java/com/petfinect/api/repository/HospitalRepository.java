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
}
