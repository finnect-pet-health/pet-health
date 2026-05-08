package com.petfinect.api.integration.kakao;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class MockKakaoOAuthClientTest {

	private final MockKakaoOAuthClient client = new MockKakaoOAuthClient();

	@Test
	void exchangeCode_validPattern_returnsKakaoUser() {
		KakaoUser user = client.exchangeCode("mock-user-1", "http://localhost/callback");

		assertThat(user.kakaoId()).isEqualTo("mock_1");
		assertThat(user.name()).isEqualTo("테스트유저1");
		assertThat(user.email()).isEqualTo("mock1@example.test");
		assertThat(user.profileImage()).isNull();
	}

	@Test
	void exchangeCode_invalidPattern_throws() {
		assertThatThrownBy(() -> client.exchangeCode("not-a-mock-code", "http://localhost"))
			.isInstanceOf(KakaoExchangeException.class)
			.hasMessageContaining("invalid_code");
	}

	@Test
	void exchangeCode_differentN_givesDifferentUser() {
		KakaoUser u1 = client.exchangeCode("mock-user-1", "http://localhost");
		KakaoUser u2 = client.exchangeCode("mock-user-42", "http://localhost");

		assertThat(u1.kakaoId()).isNotEqualTo(u2.kakaoId());
		assertThat(u2.name()).isEqualTo("테스트유저42");
	}
}
