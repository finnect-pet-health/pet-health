package com.petfinect.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import com.petfinect.api.security.JwtAuthenticationFilter;
import com.petfinect.api.security.JwtTokenProvider;

/**
 * Phase 3 — JWT Bearer 필터 + STATELESS 세션 + 라우트 권한.
 *
 * <h3>Spring Security 6 DSL</h3>
 * <ul>
 *   <li>{@code SecurityFilterChain} 빈을 등록하면 그것이 표준. {@code WebSecurityConfigurerAdapter} 는 deprecated.</li>
 *   <li>{@code .csrf().disable()} — REST API + JWT 면 CSRF 토큰 불필요.</li>
 *   <li>{@code SessionCreationPolicy.STATELESS} — 서버측 세션 없음 = JWT 만 신뢰.</li>
 *   <li>{@code addFilterBefore} — 우리 JWT 필터를 username/password 필터 앞에 끼워 넣음.</li>
 *   <li>{@code httpStatusEntryPoint(401)} — 인증 누락 시 401 응답 (기본은 form 로그인 redirect).</li>
 * </ul>
 *
 * <h3>permitAll 라우트</h3>
 * <ul>
 *   <li>{@code /actuator/health}, {@code /healthz} — 헬스체크</li>
 *   <li>{@code /v1/auth/**} — 로그인/리프레시/로그아웃 (토큰 없는 상태에서 호출)</li>
 *   <li>{@code /v3/api-docs/**}, {@code /swagger-ui/**} — OpenAPI</li>
 * </ul>
 */
@Configuration
public class SecurityConfig {

	private final JwtTokenProvider tokenProvider;

	public SecurityConfig(JwtTokenProvider tokenProvider) {
		this.tokenProvider = tokenProvider;
	}

	@Bean
	public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
		http
			.csrf(csrf -> csrf.disable())
			.sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
			.authorizeHttpRequests(auth -> auth
				.requestMatchers(
					"/actuator/health/**",
					"/actuator/info",
					"/healthz",
					"/v1/auth/**",
					"/v3/api-docs/**",
					"/swagger-ui/**",
					"/swagger-ui.html"
				).permitAll()
				.anyRequest().authenticated()
			)
			.exceptionHandling(eh -> eh
				.authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED))
			)
			.addFilterBefore(
				new JwtAuthenticationFilter(tokenProvider),
				UsernamePasswordAuthenticationFilter.class
			);
		return http.build();
	}
}
