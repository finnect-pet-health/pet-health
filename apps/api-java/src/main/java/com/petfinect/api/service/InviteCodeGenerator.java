package com.petfinect.api.service;

import java.security.SecureRandom;

import org.springframework.stereotype.Component;

/**
 * 8자 base32 초대 코드 생성기.
 *
 * <h3>Python 구현</h3>
 * <pre>{@code
 *   raw = secrets.token_bytes(5)           # 40 bits
 *   code = base64.b32encode(raw).decode().rstrip("=")
 * }</pre>
 *
 * <h3>Java 동등 구현</h3>
 * <ul>
 *   <li>{@link SecureRandom} 5 bytes → 40 bits → base32 8 chars (5 bits each).</li>
 *   <li>표준 base32 alphabet: {@code A-Z 2-7} (RFC 4648).</li>
 *   <li>학습 포인트: Java 표준 라이브러리에 base32 가 없음 → 직접 구현.
 *       (Apache Commons Codec 추가하면 한 줄이지만 외부 의존성 회피.)</li>
 * </ul>
 */
@Component
public class InviteCodeGenerator {

	private static final char[] ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567".toCharArray();
	private final SecureRandom random = new SecureRandom();

	public String generate() {
		byte[] raw = new byte[5];
		random.nextBytes(raw);
		return encodeBase32_5bytes(raw);
	}

	private static String encodeBase32_5bytes(byte[] b) {
		// 40 bits → 8 base32 chars; 각 char 는 5 bits.
		long bits = 0L;
		for (int i = 0; i < 5; i++) {
			bits = (bits << 8) | (b[i] & 0xFFL);
		}
		char[] out = new char[8];
		for (int i = 7; i >= 0; i--) {
			out[i] = ALPHABET[(int) (bits & 0x1F)];
			bits >>= 5;
		}
		return new String(out);
	}
}
