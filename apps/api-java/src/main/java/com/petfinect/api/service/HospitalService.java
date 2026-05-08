package com.petfinect.api.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.repository.HospitalRepository;
import com.petfinect.api.repository.HospitalRepository.NearbyProjection;
import com.petfinect.api.web.dto.HospitalNearbyResponse;

/**
 * 동물병원 도메인 서비스.
 *
 * <h3>PostGIS native query 사용</h3>
 * <ul>
 *   <li>{@code ST_DWithin} / {@code ST_Distance} / {@code ST_X} / {@code ST_Y} 는 JPQL 표준 함수
 *       아님 → native SQL 가 가독성/안정성에서 우월.</li>
 *   <li>{@code geography} 캐스트로 m 단위 정확한 거리 (Mercator 왜곡 회피).</li>
 * </ul>
 */
@Service
public class HospitalService {

	private final HospitalRepository hospitalRepository;

	public HospitalService(HospitalRepository hospitalRepository) {
		this.hospitalRepository = hospitalRepository;
	}

	@Transactional(readOnly = true)
	public List<HospitalNearbyResponse> findNearby(double lat, double lng, int radiusM, int limit) {
		List<NearbyProjection> rows = hospitalRepository.findNearby(lat, lng, radiusM, limit);
		return rows.stream()
			.map(p -> new HospitalNearbyResponse(
				p.getId(),
				p.getMgmtNo(),
				p.getName(),
				p.getRoadAddr(),
				p.getTel(),
				p.getLat(),
				p.getLng(),
				p.getDistanceM()
			))
			.toList();
	}
}
