package com.petfinect.api.web;

import java.util.List;

import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.petfinect.api.service.HospitalService;
import com.petfinect.api.web.dto.HospitalNearbyResponse;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * 동물병원 라우트 — Python {@code apps/api/app/api/v1/hospitals.py} 와 동일.
 *
 * <h3>Bean Validation on @RequestParam</h3>
 * <ul>
 *   <li>Spring Boot 3+ 는 클래스 레벨 {@code @Validated} 없이도 method-level 제약 동작.</li>
 *   <li>제약 위반 시 {@link jakarta.validation.ConstraintViolationException} →
 *       {@link com.petfinect.api.web.exception.GlobalExceptionHandler} 가 400 변환 (별도 핸들러 필요).</li>
 *   <li>학습 자료에선 단순화: 검증 실패 시 컨테이너가 default 400 반환.</li>
 * </ul>
 *
 * <h3>인증 정책</h3>
 * <ul>
 *   <li>현재 위치 기반 검색은 모바일 부팅 직후 (로그인 전) 도 사용 가능해야 → public.</li>
 *   <li>{@link com.petfinect.api.config.SecurityConfig} 의 permitAll 목록에 추가.</li>
 * </ul>
 */
@RestController
@RequestMapping("/v1/hospitals")
@Validated  // method param 의 @Min/@Max 활성화 — 위반시 ConstraintViolationException
public class HospitalController {

	private final HospitalService hospitalService;

	public HospitalController(HospitalService hospitalService) {
		this.hospitalService = hospitalService;
	}

	@GetMapping("/nearby")
	public List<HospitalNearbyResponse> nearby(
		@RequestParam @Min(-90) @Max(90) double lat,
		@RequestParam @Min(-180) @Max(180) double lng,
		@RequestParam(name = "radius_m", defaultValue = "3000") @Min(1) @Max(50000) int radiusM,
		@RequestParam(defaultValue = "3") @Min(1) @Max(50) int limit,
		@RequestParam(required = false) String specialty
	) {
		// specialty 는 W4-v2 에서 사용 — Phase 5 에선 무시 (Python 동일).
		return hospitalService.findNearby(lat, lng, radiusM, limit);
	}
}
