package com.petfinect.api.integration.aiserver;

import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * HMAC-SHA256 헬퍼.
 *
 * <p>스킴: {@code hex(HMAC-SHA256(shared_secret, raw_bytes))}.
 * AI 서버 ({@code apps/ai-server/app/security/hmac_auth.py}) 가 동일 알고리즘으로 검증.
 *
 * <h3>학습 포인트</h3>
 * <ul>
 *   <li>Python 의 {@code hmac.new(key, body, hashlib.sha256).hexdigest()} → Java {@code Mac.getInstance("HmacSHA256")}.</li>
 *   <li>{@code MessageDigest.isEqual} = constant-time 비교 (timing attack 방어). Python 의
 *       {@code hmac.compare_digest} 와 동일 역할.</li>
 *   <li>HMAC 객체는 thread-safe 가 아님 — 호출마다 새로 생성.</li>
 * </ul>
 */
public final class HmacSigner {

	private static final String ALGO = "HmacSHA256";

	private final byte[] secret;

	public HmacSigner(String secret) {
		if (secret == null || secret.isEmpty()) {
			throw new IllegalArgumentException("HMAC secret 은 비어 있을 수 없음");
		}
		this.secret = secret.getBytes(StandardCharsets.UTF_8);
	}

	/**
	 * {@code body} 의 HMAC-SHA256 hex digest.
	 */
	public String signHex(byte[] body) {
		try {
			Mac mac = Mac.getInstance(ALGO);
			mac.init(new SecretKeySpec(secret, ALGO));
			return toHex(mac.doFinal(body));
		} catch (NoSuchAlgorithmException | InvalidKeyException e) {
			// HmacSHA256 미지원 JVM 은 사실상 없음 — RuntimeException 으로 wrap.
			throw new IllegalStateException("HMAC-SHA256 init 실패", e);
		}
	}

	/**
	 * 헤더값과 본문 HMAC 비교 (constant-time).
	 */
	public boolean verifyHex(byte[] body, String hexDigest) {
		if (hexDigest == null) {
			return false;
		}
		String expected = signHex(body);
		return MessageDigest.isEqual(
			expected.getBytes(StandardCharsets.US_ASCII),
			hexDigest.getBytes(StandardCharsets.US_ASCII)
		);
	}

	private static String toHex(byte[] bytes) {
		StringBuilder sb = new StringBuilder(bytes.length * 2);
		for (byte b : bytes) {
			sb.append(Character.forDigit((b >> 4) & 0xF, 16));
			sb.append(Character.forDigit(b & 0xF, 16));
		}
		return sb.toString();
	}
}
