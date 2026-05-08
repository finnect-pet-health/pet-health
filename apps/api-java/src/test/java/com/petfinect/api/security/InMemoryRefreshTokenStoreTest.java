package com.petfinect.api.security;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.Test;

class InMemoryRefreshTokenStoreTest {

	@Test
	void issue_thenRotate_returnsNewTokenAndUserId() {
		InMemoryRefreshTokenStore store = new InMemoryRefreshTokenStore(14);
		UUID userId = UUID.randomUUID();

		String token = store.issue(userId);
		Optional<RefreshTokenStore.RotationResult> rotated = store.rotate(token);

		assertThat(rotated).isPresent();
		assertThat(rotated.get().userId()).isEqualTo(userId);
		assertThat(rotated.get().newToken()).isNotEqualTo(token);
	}

	@Test
	void rotate_oldTokenRevokedAfterRotation() {
		InMemoryRefreshTokenStore store = new InMemoryRefreshTokenStore(14);
		String token = store.issue(UUID.randomUUID());

		store.rotate(token);
		Optional<RefreshTokenStore.RotationResult> second = store.rotate(token);

		assertThat(second).isEmpty();
	}

	@Test
	void revoke_isIdempotent() {
		InMemoryRefreshTokenStore store = new InMemoryRefreshTokenStore(14);
		String token = store.issue(UUID.randomUUID());

		store.revoke(token);
		store.revoke(token); // 두 번 호출해도 예외 없음
	}

	@Test
	void rotate_unknownToken_returnsEmpty() {
		InMemoryRefreshTokenStore store = new InMemoryRefreshTokenStore(14);

		Optional<RefreshTokenStore.RotationResult> result = store.rotate("never-issued");

		assertThat(result).isEmpty();
	}
}
