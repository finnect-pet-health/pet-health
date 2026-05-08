package com.petfinect.api.integration.aiserver;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;

import javax.net.ssl.SSLContext;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * mTLS context 빌더 — PKCS#1 거부 + 누락 파일 거부 + 실 PEM 파싱 smoke.
 *
 * <p>실 mTLS handshake 자체는 {@link RealAIServerClientHttpTest} 가 무관 (HTTP) 으로 분리.
 * 본 슬라이스는 cert/key 파싱 분기 + 에러 메시지 정합성에 한정.
 *
 * <p>{@code src/test/resources/aiserver/test-ca.crt} 는 {@code openssl req -x509 -newkey rsa:2048
 * -nodes} 로 발급한 self-signed CA. 실제 handshake 를 수행하지 않으므로 만료/CN 무관 — 단지
 * Java {@link java.security.cert.CertificateFactory} 가 X.509 로 인식할 수 있는 PEM 형식이면 충분.
 */
class MtlsSslContextFactoryTest {

	@Test
	void buildTrustOnly_acceptsValidCaPem(@TempDir Path tmp) throws IOException {
		Path ca = copyClasspathPem("aiserver/test-ca.crt", tmp.resolve("ca.crt"));

		SSLContext ctx = MtlsSslContextFactory.buildTrustOnly(ca);
		assertThat(ctx).isNotNull();
		assertThat(ctx.getProtocol()).isEqualTo("TLS");
	}

	@Test
	void buildTrustOnly_missingCaFile_throws(@TempDir Path tmp) {
		assertThatThrownBy(() -> MtlsSslContextFactory.buildTrustOnly(tmp.resolve("missing.crt")))
			.isInstanceOf(AIServerException.class);
	}

	@Test
	void buildTrustOnly_emptyPem_throws(@TempDir Path tmp) throws IOException {
		Path empty = tmp.resolve("empty.crt");
		Files.writeString(empty, "");
		assertThatThrownBy(() -> MtlsSslContextFactory.buildTrustOnly(empty))
			.isInstanceOf(AIServerException.class);
	}

	@Test
	void build_pkcs1KeyRejectedWithGuidance(@TempDir Path tmp) throws IOException {
		Path ca = copyClasspathPem("aiserver/test-ca.crt", tmp.resolve("ca.crt"));
		Path cert = copyClasspathPem("aiserver/test-ca.crt", tmp.resolve("client.crt"));
		Path key = tmp.resolve("client.key");
		Files.writeString(key, "-----BEGIN RSA PRIVATE KEY-----\nMIIBOg==\n-----END RSA PRIVATE KEY-----\n");

		assertThatThrownBy(() -> MtlsSslContextFactory.build(ca, cert, key))
			.isInstanceOf(AIServerException.class)
			.hasMessageContaining("PKCS#8");
	}

	private static Path copyClasspathPem(String resource, Path target) throws IOException {
		try (InputStream in = MtlsSslContextFactoryTest.class.getClassLoader()
				.getResourceAsStream(resource)) {
			if (in == null) {
				throw new IllegalStateException("test resource not found: " + resource);
			}
			Files.write(target, in.readAllBytes());
		}
		return target;
	}
}
