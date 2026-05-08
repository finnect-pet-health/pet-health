package com.petfinect.api.security;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import javax.crypto.SecretKey;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

/**
 * HS256 JWT 발급/검증.
 *
 * <h3>Python {@code app.security.jwt} 와 동일 contract</h3>
 * <ul>
 *   <li>algorithm: HS256</li>
 *   <li>claims: {@code sub} (user UUID 문자열), {@code fids} (UUID 문자열 list),
 *       {@code roles} (Map&lt;String, String&gt; — fid 문자열 → role), {@code exp} (unix sec)</li>
 *   <li>secret: {@code petfinect.jwt.secret} 설정에서 주입. 32 bytes 이상 권장.</li>
 *   <li>access TTL: {@code petfinect.jwt.access-ttl-min} 분 (기본 15)</li>
 * </ul>
 *
 * <h3>JJWT 0.12 API 메모</h3>
 * <ul>
 *   <li>{@code Jwts.builder()} → {@code subject(...)} / {@code claim(...)} / {@code expiration(...)} / {@code signWith(key)}</li>
 *   <li>{@code Jwts.parser().verifyWith(key).build().parseSignedClaims(token)} → 검증 + 파싱</li>
 *   <li>실패 시 {@link JwtException} 계열 — {@code ExpiredJwtException}, {@code SignatureException} 등.</li>
 * </ul>
 */
@Component
public class JwtTokenProvider {

	private final SecretKey key;
	private final long accessTtlSeconds;

	public JwtTokenProvider(
		@Value("${petfinect.jwt.secret}") String secret,
		@Value("${petfinect.jwt.access-ttl-min:15}") int accessTtlMin
	) {
		this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
		this.accessTtlSeconds = (long) accessTtlMin * 60;
	}

	public String encodeAccess(UUID userId, List<UUID> fids, Map<UUID, String> roles) {
		Instant now = Instant.now();
		Instant exp = now.plusSeconds(accessTtlSeconds);

		List<String> fidStrings = fids.stream().map(UUID::toString).toList();
		Map<String, String> roleStrings = new HashMap<>();
		roles.forEach((k, v) -> roleStrings.put(k.toString(), v));

		return Jwts.builder()
			.subject(userId.toString())
			.claim("fids", fidStrings)
			.claim("roles", roleStrings)
			.issuedAt(java.util.Date.from(now))
			.expiration(java.util.Date.from(exp))
			.signWith(key)
			.compact();
	}

	@SuppressWarnings("unchecked")
	public AccessClaims decodeAccess(String token) {
		Jws<Claims> jws = Jwts.parser()
			.verifyWith(key)
			.build()
			.parseSignedClaims(token);
		Claims body = jws.getPayload();

		UUID sub = UUID.fromString(body.getSubject());
		List<String> fidStrings = body.get("fids", List.class);
		List<UUID> fids = fidStrings == null ? List.of() : fidStrings.stream().map(UUID::fromString).toList();

		Map<String, String> rolesRaw = body.get("roles", Map.class);
		Map<UUID, String> roles = new HashMap<>();
		if (rolesRaw != null) {
			rolesRaw.forEach((k, v) -> roles.put(UUID.fromString(k), v));
		}

		long exp = body.getExpiration().toInstant().getEpochSecond();
		return new AccessClaims(sub, fids, roles, exp);
	}
}
