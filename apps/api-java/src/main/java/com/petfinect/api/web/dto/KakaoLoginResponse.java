package com.petfinect.api.web.dto;

/**
 * {@code POST /v1/auth/kakao} 응답 — access + refresh + user.
 */
public record KakaoLoginResponse(
	String access,
	String refresh,
	UserSummary user
) {}
