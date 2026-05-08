package com.petfinect.api.security;

import java.io.IOException;
import java.util.List;

import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/**
 * Bearer 토큰을 SecurityContext 에 설정하는 필터.
 *
 * <h3>OncePerRequestFilter</h3>
 * <ul>
 *   <li>요청당 1회 실행 보장 — forward/include 시 중복 실행 방지.</li>
 *   <li>Servlet Filter 의 표준 base class. {@code doFilterInternal} 만 구현.</li>
 * </ul>
 *
 * <h3>흐름</h3>
 * <ol>
 *   <li>{@code Authorization: Bearer {token}} 헤더 추출. 없으면 통과 (downstream 이 401).</li>
 *   <li>{@link JwtTokenProvider#decodeAccess} 로 검증.</li>
 *   <li>성공: {@link AuthenticatedUser} 를 principal 로 SecurityContext 에 셋.</li>
 *   <li>실패: SecurityContext 비워둠 → 보호된 endpoint 는 401 반환.
 *       (인증 실패시 즉시 401 보내는 대신 downstream 에 위임 — entry point 가 처리)</li>
 * </ol>
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {

	private static final String BEARER_PREFIX = "Bearer ";
	private final JwtTokenProvider tokenProvider;

	public JwtAuthenticationFilter(JwtTokenProvider tokenProvider) {
		this.tokenProvider = tokenProvider;
	}

	@Override
	protected void doFilterInternal(
		HttpServletRequest request,
		HttpServletResponse response,
		FilterChain filterChain
	) throws ServletException, IOException {
		String header = request.getHeader("Authorization");
		if (header != null && header.startsWith(BEARER_PREFIX)) {
			String token = header.substring(BEARER_PREFIX.length());
			try {
				AccessClaims claims = tokenProvider.decodeAccess(token);
				AuthenticatedUser principal = new AuthenticatedUser(claims);
				SecurityContextHolder.getContext().setAuthentication(principal);
			} catch (JwtException ignored) {
				// 무효 토큰 → SecurityContext 비워둠. 보호 endpoint 가 401.
			}
		}
		filterChain.doFilter(request, response);
	}

	/**
	 * Spring Security {@code Authentication} 구현 — {@code @AuthenticationPrincipal}
	 * 으로 컨트롤러에서 직접 받을 수 있게 됨.
	 */
	public static final class AuthenticatedUser extends AbstractAuthenticationToken {
		private final AccessClaims claims;

		public AuthenticatedUser(AccessClaims claims) {
			super(List.of()); // authorities — RBAC 는 claims.roles 로 직접 검사
			this.claims = claims;
			setAuthenticated(true);
		}

		public AccessClaims claims() {
			return claims;
		}

		@Override
		public Object getCredentials() {
			return null;
		}

		@Override
		public Object getPrincipal() {
			// {@code @AuthenticationPrincipal AuthenticatedUser} 가 동작하려면
			// principal 자체가 이 객체여야 함 — Spring Security 의 표준 패턴.
			return this;
		}

		@Override
		public String getName() {
			return claims.sub().toString();
		}
	}
}
