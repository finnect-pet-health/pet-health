package com.petfinect.api.security;

import java.util.Optional;
import java.util.UUID;

/**
 * Refresh token 저장소 인터페이스.
 *
 * <h3>왜 인터페이스로 분리했는가</h3>
 * <ul>
 *   <li>Python 은 Redis 인스턴스를 직접 주입하지만 (apps/api), Java 는 인터페이스 →
 *       in-memory 구현 (학습/테스트) ↔ Redis 구현 (운영) 교체가 명료.</li>
 *   <li>Hexagonal architecture 의 port/adapter 패턴 — 비즈니스 로직 (AuthService) 은
 *       저장소 구현체를 모름.</li>
 * </ul>
 *
 * <h3>contract</h3>
 * <ul>
 *   <li>{@code issue}: opaque token 발급 + TTL 동안 유지</li>
 *   <li>{@code rotate}: 기존 token 삭제 + 새 token 발급 (one-time use)</li>
 *   <li>{@code revoke}: 명시적 logout. 멱등 — 이미 없어도 예외 안 던짐.</li>
 * </ul>
 */
public interface RefreshTokenStore {

	/**
	 * @return 새로 발급된 opaque token 문자열
	 */
	String issue(UUID userId);

	/**
	 * @param token 클라이언트가 제출한 refresh token
	 * @return 토큰이 유효하면 새 token + userId, 무효하면 {@link Optional#empty()}
	 */
	Optional<RotationResult> rotate(String token);

	/**
	 * 멱등 — 이미 없어도 OK.
	 */
	void revoke(String token);

	record RotationResult(String newToken, UUID userId) {}
}
