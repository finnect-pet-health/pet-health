package com.petfinect.api.web.dto;

import java.time.LocalDate;
import java.util.List;

import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

/**
 * {@code POST /v1/families/{familyId}/pets} 요청 body.
 *
 * <p>모든 필드 optional — 처음 등록 시 점진 입력. 이후 PATCH 로 보강.
 * V5 부터 {@code name} 추가 (nullable, 모바일 점진 도입).
 */
public record PetCreateRequest(
	@Size(max = 50) String name,
	@Size(max = 50) String breed,
	LocalDate dob,
	@Positive Double weight,
	Boolean neutered,
	List<String> conditions
) {}
