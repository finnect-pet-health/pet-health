package com.petfinect.api.web.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * {@code POST /v1/auth/kakao} 요청 body.
 *
 * <h3>Bean Validation</h3>
 * <ul>
 *   <li>{@code @NotBlank} — null 도, 공백문자열도 거부. 컨트롤러에서 {@code @Valid} 가
 *       이걸 자동 검증 → 400 응답.</li>
 *   <li>Python pydantic 의 필드 검증과 동일 자리. 학습 포인트: Java 는 어노테이션 기반,
 *       Python 은 타입힌트+제약 기반.</li>
 * </ul>
 */
public record KakaoLoginRequest(
	@NotBlank String authCode,
	@NotBlank String redirectUri
) {}
