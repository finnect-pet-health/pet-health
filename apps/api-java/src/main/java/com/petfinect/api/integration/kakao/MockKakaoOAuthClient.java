package com.petfinect.api.integration.kakao;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 결정론적 카카오 mock — 테스트/개발 환경 전용.
 *
 * <p>패턴: {@code mock-user-{N}} → KakaoUser(kakaoId=mock_{N}, name=테스트유저{N}, …)
 * Python {@code apps/api/app/integrations/kakao/mock.py} 와 동일 contract.
 *
 * <h3>주의</h3>
 * <ul>
 *   <li>{@code @Component} 마킹하지 않고 {@link KakaoOAuthClientConfig} 에서
 *       조건부 {@code @Bean} 으로 등록 → 환경에 따라 Real/Mock 자동 분기.</li>
 * </ul>
 */
public class MockKakaoOAuthClient implements KakaoOAuthClient {

	private static final Pattern PATTERN = Pattern.compile("^mock-user-(\\d+)$");

	@Override
	public KakaoUser exchangeCode(String code, String redirectUri) {
		Matcher m = PATTERN.matcher(code);
		if (!m.matches()) {
			throw new KakaoExchangeException("invalid_code");
		}
		String n = m.group(1);
		return new KakaoUser(
			"mock_" + n,
			"테스트유저" + n,
			"mock" + n + "@example.test",
			null
		);
	}
}
