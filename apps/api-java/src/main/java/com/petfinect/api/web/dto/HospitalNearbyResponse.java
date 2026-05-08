package com.petfinect.api.web.dto;

import java.util.UUID;

/**
 * {@code GET /v1/hospitals/nearby} 응답 — Python {@code HospitalNearby} 와 schema 동일.
 *
 * <ul>
 *   <li>{@code lat}/{@code lng} 은 PostGIS POINT 에서 {@code ST_Y}/{@code ST_X} 로 추출.</li>
 *   <li>{@code distanceM} 은 {@code geography} 캐스트 후 {@code ST_Distance} 의 m 단위 결과.</li>
 * </ul>
 */
public record HospitalNearbyResponse(
	UUID id,
	String mgmtNo,
	String name,
	String roadAddr,
	String tel,
	double lat,
	double lng,
	double distanceM
) {}
