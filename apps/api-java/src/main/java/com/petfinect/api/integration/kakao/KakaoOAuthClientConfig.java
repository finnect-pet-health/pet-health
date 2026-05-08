package com.petfinect.api.integration.kakao;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

/**
 * 환경별 KakaoOAuthClient 빈 분기 — Python factory 패턴의 Java 버전.
 *
 * <h3>Spring profile 기반 분기</h3>
 * <ul>
 *   <li>{@code @Profile("!production")} — production 이 아닌 모든 프로필에서 Mock 사용.</li>
 *   <li>{@code @Profile("production")} — 운영에서만 Real 빈 등록.</li>
 *   <li>학습 포인트: Python 에서는 함수 안에서 환경변수 검사하지만, Java/Spring 은
 *       프로필을 통한 선언적 분기가 더 자연스러움.</li>
 * </ul>
 *
 * <h3>대안</h3>
 * <ul>
 *   <li>{@code @ConditionalOnProperty(name = "petfinect.kakao.use-mock", havingValue = "true")}
 *       — 단일 환경변수로 분기 가능. Python 의 {@code KAKAO_USE_MOCK} 와 1:1.</li>
 * </ul>
 */
@Configuration
public class KakaoOAuthClientConfig {

	@Bean
	@Profile("!production")
	public KakaoOAuthClient mockKakaoOAuthClient() {
		return new MockKakaoOAuthClient();
	}

	@Bean
	@Profile("production")
	public KakaoOAuthClient realKakaoOAuthClient(
		@Value("${petfinect.kakao.rest-api-key:}") String restApiKey,
		@Value("${petfinect.kakao.client-secret:}") String clientSecret
	) {
		return new RealKakaoOAuthClient(restApiKey, clientSecret);
	}
}
