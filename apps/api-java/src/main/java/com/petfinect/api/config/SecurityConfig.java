package com.petfinect.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Phase 0 임시 보안 설정 — 모든 요청 허용 (헬스체크 검증용).
 *
 * Phase 3 에서 다음으로 교체:
 * - JWT Bearer 필터 (HS256, sub=user_id, fids list, roles map)
 * - /v1/auth/** permitAll, 그 외 authenticated
 * - SessionCreationPolicy.STATELESS
 * - CORS, CSRF 비활성 (REST API)
 */
@Configuration
public class SecurityConfig {

	@Bean
	public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
		http
			.csrf(csrf -> csrf.disable())
			.sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
			.authorizeHttpRequests(auth -> auth.anyRequest().permitAll());
		return http.build();
	}
}
