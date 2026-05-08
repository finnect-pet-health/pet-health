package com.petfinect.api.web.dto;

import java.util.UUID;

/**
 * 인증 응답에 포함되는 사용자 요약 — Python {@code UserOut} 과 동일 schema.
 */
public record UserSummary(
	UUID id,
	String name,
	String profileImage
) {}
