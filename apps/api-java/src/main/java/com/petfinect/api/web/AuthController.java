package com.petfinect.api.web;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.petfinect.api.integration.kakao.KakaoExchangeException;
import com.petfinect.api.service.AuthService;
import com.petfinect.api.web.dto.KakaoLoginRequest;
import com.petfinect.api.web.dto.KakaoLoginResponse;
import com.petfinect.api.web.dto.RefreshRequest;
import com.petfinect.api.web.dto.TokenPair;
import com.petfinect.api.web.exception.ApiException;

import jakarta.validation.Valid;

/**
 * 인증 엔드포인트 — Python {@code apps/api/app/api/v1/auth.py} 와 contract 동일.
 *
 * <h3>Spring MVC 컨트롤러 패턴</h3>
 * <ul>
 *   <li>{@code @RestController}: {@code @Controller} + {@code @ResponseBody} 합성.
 *       모든 메서드 응답을 JSON 직렬화.</li>
 *   <li>{@code @RequestMapping("/v1/auth")}: 클래스 레벨 prefix.</li>
 *   <li>{@code @PostMapping("/kakao")}: HTTP 메서드 매핑.</li>
 *   <li>{@code @RequestBody @Valid}: JSON 역직렬화 + Bean Validation 트리거 →
 *       실패시 {@link org.springframework.web.bind.MethodArgumentNotValidException}.</li>
 * </ul>
 */
@RestController
@RequestMapping("/v1/auth")
public class AuthController {

	private final AuthService authService;

	public AuthController(AuthService authService) {
		this.authService = authService;
	}

	@PostMapping("/kakao")
	public KakaoLoginResponse kakaoLogin(@Valid @RequestBody KakaoLoginRequest req) {
		try {
			return authService.loginWithKakao(req.authCode(), req.redirectUri());
		} catch (KakaoExchangeException exc) {
			throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_CODE", exc.getMessage());
		}
	}

	@PostMapping("/refresh")
	public TokenPair refresh(@Valid @RequestBody RefreshRequest req) {
		return authService.refresh(req.refresh());
	}

	@PostMapping("/logout")
	public ResponseEntity<Void> logout(@Valid @RequestBody RefreshRequest req) {
		authService.logout(req.refresh());
		return ResponseEntity.noContent().build();
	}
}
