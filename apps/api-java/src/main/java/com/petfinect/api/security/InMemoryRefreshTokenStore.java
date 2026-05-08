package com.petfinect.api.security;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * 학습용 in-memory refresh token 저장소.
 *
 * <h3>운영에선 부적합</h3>
 * <ul>
 *   <li>인스턴스 재시작 시 모든 토큰 손실 → 사용자 강제 재로그인.</li>
 *   <li>다중 인스턴스 sticky session 필요 → 수평확장 막힘.</li>
 *   <li>운영용은 Redis 기반 구현체 별도 제공해야 함 (예: {@code RedisRefreshTokenStore}).</li>
 * </ul>
 *
 * <h3>학습 포인트</h3>
 * <ul>
 *   <li>{@link ConcurrentHashMap} — Java 의 thread-safe map. Spring 빈은 기본
 *       singleton 이고 멀티스레드 요청 처리하므로 동시성 안전 자료구조 필수.</li>
 *   <li>만료 청소: {@link System#currentTimeMillis()} 기반 lazy expiry — 조회 시 만료된 항목
 *       발견하면 제거. 운영용 Redis 는 이걸 자동.</li>
 * </ul>
 */
@Component
public class InMemoryRefreshTokenStore implements RefreshTokenStore {

	private final long ttlSeconds;
	private final ConcurrentHashMap<String, Entry> tokens = new ConcurrentHashMap<>();

	public InMemoryRefreshTokenStore(
		@Value("${petfinect.jwt.refresh-ttl-days:14}") int refreshTtlDays
	) {
		this.ttlSeconds = (long) refreshTtlDays * 24 * 3600;
	}

	@Override
	public String issue(UUID userId) {
		String token = UUID.randomUUID().toString();
		long expiresAt = Instant.now().getEpochSecond() + ttlSeconds;
		tokens.put(token, new Entry(userId, expiresAt));
		return token;
	}

	@Override
	public Optional<RotationResult> rotate(String token) {
		Entry entry = tokens.remove(token);
		if (entry == null || entry.expiresAt < Instant.now().getEpochSecond()) {
			return Optional.empty();
		}
		String newToken = issue(entry.userId);
		return Optional.of(new RotationResult(newToken, entry.userId));
	}

	@Override
	public void revoke(String token) {
		tokens.remove(token);
	}

	private record Entry(UUID userId, long expiresAt) {}
}
