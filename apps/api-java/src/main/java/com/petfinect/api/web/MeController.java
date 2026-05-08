package com.petfinect.api.web;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.petfinect.api.security.JwtAuthenticationFilter.AuthenticatedUser;
import com.petfinect.api.service.MeService;
import com.petfinect.api.web.dto.MeResponse;

/**
 * 현재 사용자 정보 조회 — Python {@code GET /v1/me} 동일 contract.
 *
 * <h3>{@code @AuthenticationPrincipal}</h3>
 * <ul>
 *   <li>SecurityContext 의 principal 을 자동 주입. {@link com.petfinect.api.security.JwtAuthenticationFilter}
 *       가 셋한 {@link AuthenticatedUser} 가 들어옴.</li>
 *   <li>인증 안 된 요청은 SecurityConfig 의 {@code anyRequest().authenticated()} 가 막아 401.</li>
 *   <li>Python 의 {@code Depends(current_user)} 와 동일 자리.</li>
 * </ul>
 */
@RestController
@RequestMapping("/v1")
public class MeController {

	private final MeService meService;

	public MeController(MeService meService) {
		this.meService = meService;
	}

	@GetMapping("/me")
	public MeResponse me(@AuthenticationPrincipal AuthenticatedUser principal) {
		return meService.loadMe(principal.claims().sub());
	}
}
