package com.petfinect.api.integration.aiserver;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

/**
 * HMAC-SHA256 서명/검증 — Python {@code hmac_auth.py} 와 byte-for-byte 일치 검증.
 *
 * <h3>테스트 벡터</h3>
 * <ul>
 *   <li>RFC 4231-style: key="key", body=The quick brown fox… → 알려진 hex digest.</li>
 *   <li>Python {@code hmac.new(b"key", body, hashlib.sha256).hexdigest()} 와 동일 출력.</li>
 * </ul>
 */
class HmacSignerTest {

	private static final String KEY = "key";
	private static final byte[] BODY =
		"The quick brown fox jumps over the lazy dog".getBytes(StandardCharsets.UTF_8);
	private static final String EXPECTED =
		"f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8";

	@Test
	void signHex_matchesRfcVector() {
		String actual = new HmacSigner(KEY).signHex(BODY);
		assertThat(actual).isEqualTo(EXPECTED);
	}

	@Test
	void verifyHex_acceptsCorrectDigest() {
		HmacSigner signer = new HmacSigner(KEY);
		assertThat(signer.verifyHex(BODY, EXPECTED)).isTrue();
	}

	@Test
	void verifyHex_rejectsTamperedDigest() {
		HmacSigner signer = new HmacSigner(KEY);
		String tampered = EXPECTED.substring(0, EXPECTED.length() - 1) + "0";
		assertThat(signer.verifyHex(BODY, tampered)).isFalse();
	}

	@Test
	void verifyHex_rejectsTamperedBody() {
		HmacSigner signer = new HmacSigner(KEY);
		byte[] tampered = "The quick brown fox jumps over the lazy DOG".getBytes(StandardCharsets.UTF_8);
		assertThat(signer.verifyHex(tampered, EXPECTED)).isFalse();
	}

	@Test
	void verifyHex_rejectsNullDigest() {
		assertThat(new HmacSigner(KEY).verifyHex(BODY, null)).isFalse();
	}

	@Test
	void emptySecret_throws() {
		assertThatThrownBy(() -> new HmacSigner(""))
			.isInstanceOf(IllegalArgumentException.class);
		assertThatThrownBy(() -> new HmacSigner(null))
			.isInstanceOf(IllegalArgumentException.class);
	}

	@Test
	void differentSecrets_yieldDifferentDigests() {
		String a = new HmacSigner("key-a").signHex(BODY);
		String b = new HmacSigner("key-b").signHex(BODY);
		assertThat(a).isNotEqualTo(b);
	}
}
