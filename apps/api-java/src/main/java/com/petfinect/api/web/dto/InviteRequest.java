package com.petfinect.api.web.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * {@code POST /v1/families/{familyId}/invite} 요청 body.
 *
 * <p>{@code ttlHours} 는 {@code null} 이어도 OK — 서버가 기본 72h 적용.
 * 학습 포인트: Java {@code int} 는 nullable 불가 → {@link Integer} (래퍼) 사용.
 */
public record InviteRequest(
	@Min(1) @Max(24 * 30) Integer ttlHours
) {}
