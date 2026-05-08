package com.petfinect.api.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;

import io.jsonwebtoken.JwtException;

/**
 * 단위 테스트 — Spring 컨텍스트 없이 JJWT 동작만 검증.
 *
 * <p>Spring Boot 가 뜨지 않으므로 매우 빠르게 실행. JWT round-trip 의 핵심:
 * <ul>
 *   <li>encode 한 토큰이 같은 secret 으로 decode 되어 원본 클레임 복원 가능해야 함.</li>
 *   <li>잘못된 secret 으로 decode 시 {@link JwtException}.</li>
 *   <li>다중 fid/role 조합도 손실 없이 round-trip.</li>
 * </ul>
 */
class JwtTokenProviderTest {

	private static final String SECRET = "test-secret-must-be-at-least-32-bytes-long-for-hs256";

	@Test
	void roundTrip_singleFamily() {
		JwtTokenProvider provider = new JwtTokenProvider(SECRET, 15);
		UUID userId = UUID.randomUUID();
		UUID famId = UUID.randomUUID();

		String token = provider.encodeAccess(
			userId,
			List.of(famId),
			Map.of(famId, "owner")
		);

		AccessClaims claims = provider.decodeAccess(token);
		assertThat(claims.sub()).isEqualTo(userId);
		assertThat(claims.fids()).containsExactly(famId);
		assertThat(claims.roles()).containsEntry(famId, "owner");
		assertThat(claims.exp()).isGreaterThan(System.currentTimeMillis() / 1000);
	}

	@Test
	void roundTrip_multipleFamilies() {
		JwtTokenProvider provider = new JwtTokenProvider(SECRET, 15);
		UUID userId = UUID.randomUUID();
		UUID f1 = UUID.randomUUID();
		UUID f2 = UUID.randomUUID();

		String token = provider.encodeAccess(
			userId,
			List.of(f1, f2),
			Map.of(f1, "owner", f2, "member")
		);

		AccessClaims claims = provider.decodeAccess(token);
		assertThat(claims.fids()).containsExactlyInAnyOrder(f1, f2);
		assertThat(claims.roles()).containsEntry(f1, "owner").containsEntry(f2, "member");
		assertThat(claims.hasRoleIn(f1, "owner")).isTrue();
		assertThat(claims.hasRoleIn(f2, "owner", "member")).isTrue();
		assertThat(claims.hasRoleIn(f2, "owner")).isFalse();
	}

	@Test
	void wrongSecret_throws() {
		JwtTokenProvider issuer = new JwtTokenProvider(SECRET, 15);
		JwtTokenProvider verifier = new JwtTokenProvider(
			"different-secret-also-32-bytes-or-more-for-hs256",
			15
		);
		UUID userId = UUID.randomUUID();

		String token = issuer.encodeAccess(userId, List.of(), Map.of());

		assertThatThrownBy(() -> verifier.decodeAccess(token))
			.isInstanceOf(JwtException.class);
	}

	@Test
	void emptyClaims_roundTrip() {
		JwtTokenProvider provider = new JwtTokenProvider(SECRET, 15);
		UUID userId = UUID.randomUUID();

		String token = provider.encodeAccess(userId, List.of(), Map.of());

		AccessClaims claims = provider.decodeAccess(token);
		assertThat(claims.fids()).isEmpty();
		assertThat(claims.roles()).isEmpty();
	}
}
