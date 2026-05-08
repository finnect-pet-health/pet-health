package com.petfinect.api.integration.kakao;

/**
 * 카카오 OAuth 로 받아온 사용자 프로필.
 *
 * <p>Java {@code record} — Python {@code @dataclass(frozen=True) KakaoUser} 와 동일 역할.
 * email/profileImage 는 카카오 동의 항목에 따라 null 가능.
 */
public record KakaoUser(
	String kakaoId,
	String name,
	String email,
	String profileImage
) {}
