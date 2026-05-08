package com.petfinect.api.integration.aiserver;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.GeneralSecurityException;
import java.security.KeyFactory;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.Certificate;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Base64;
import java.util.Collection;

import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;

/**
 * mTLS 용 {@link SSLContext} 빌더 — PEM CA + 클라이언트 cert/key 로드.
 *
 * <p>Python {@code build_client_ssl_context} 의 Java 짝.
 *
 * <h3>지원 키 포맷</h3>
 * <ul>
 *   <li>PKCS#8 PEM ({@code -----BEGIN PRIVATE KEY-----}) — Java 표준 지원.</li>
 *   <li>PKCS#1 RSA PEM ({@code -----BEGIN RSA PRIVATE KEY-----}) 은 직접 미지원 — 변환 필요:
 *       <pre>{@code openssl pkcs8 -topk8 -nocrypt -in client.key -out client-pk8.key}</pre>
 *       {@code gen_dev_certs.sh} 산출물은 PKCS#1 이므로 위 명령으로 변환 후 사용.</li>
 * </ul>
 *
 * <h3>학습 포인트</h3>
 * <ul>
 *   <li>Java SSL 구성은 {@link KeyStore} 추상으로 표준화 — PEM 직접 지원 X.</li>
 *   <li>BouncyCastle 추가 시 PKCS#1/암호화 키도 처리 가능하나, 학습 단순성을 위해 표준 라이브러리만 사용.</li>
 *   <li>{@link KeyStore} 의 비밀번호는 in-memory 임시 저장이라 임의 값 ({@code "changeit"}) 사용.</li>
 * </ul>
 */
public final class MtlsSslContextFactory {

	private MtlsSslContextFactory() {}

	/**
	 * CA 한 개 + 클라이언트 cert chain + 클라이언트 키로 mTLS context 생성.
	 *
	 * @param caCertPem        CA 인증서 PEM 경로 (서버 cert 검증용)
	 * @param clientCertPem    클라이언트 cert PEM 경로
	 * @param clientKeyPemPk8  클라이언트 private key PKCS#8 PEM 경로
	 */
	public static SSLContext build(Path caCertPem, Path clientCertPem, Path clientKeyPemPk8) {
		try {
			TrustManagerFactory tmf = trustManager(caCertPem);
			KeyManagerFactory kmf = keyManager(clientCertPem, clientKeyPemPk8);
			SSLContext ctx = SSLContext.getInstance("TLS");
			ctx.init(kmf.getKeyManagers(), tmf.getTrustManagers(), null);
			return ctx;
		} catch (GeneralSecurityException | IOException e) {
			throw new AIServerException("mTLS SSLContext 생성 실패", e);
		}
	}

	/**
	 * 서버 cert 검증만 (CA) + 클라이언트 인증 없음 — TLS 만, mTLS X.
	 */
	public static SSLContext buildTrustOnly(Path caCertPem) {
		try {
			TrustManagerFactory tmf = trustManager(caCertPem);
			SSLContext ctx = SSLContext.getInstance("TLS");
			ctx.init(null, tmf.getTrustManagers(), null);
			return ctx;
		} catch (GeneralSecurityException | IOException e) {
			throw new AIServerException("TLS SSLContext 생성 실패", e);
		}
	}

	private static TrustManagerFactory trustManager(Path caCertPem)
			throws GeneralSecurityException, IOException {
		Collection<? extends Certificate> caCerts = parseCerts(Files.readAllBytes(caCertPem));
		KeyStore trust = KeyStore.getInstance(KeyStore.getDefaultType());
		trust.load(null, null);
		int i = 0;
		for (Certificate c : caCerts) {
			trust.setCertificateEntry("ca-" + (i++), c);
		}
		TrustManagerFactory tmf = TrustManagerFactory.getInstance(
			TrustManagerFactory.getDefaultAlgorithm()
		);
		tmf.init(trust);
		return tmf;
	}

	private static KeyManagerFactory keyManager(Path certPem, Path keyPemPk8)
			throws GeneralSecurityException, IOException {
		Collection<? extends Certificate> chain = parseCerts(Files.readAllBytes(certPem));
		PrivateKey key = parsePkcs8Key(Files.readAllBytes(keyPemPk8));

		KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
		char[] password = "changeit".toCharArray();
		ks.load(null, password);
		ks.setKeyEntry("client", key, password, chain.toArray(new Certificate[0]));

		KeyManagerFactory kmf = KeyManagerFactory.getInstance(
			KeyManagerFactory.getDefaultAlgorithm()
		);
		kmf.init(ks, password);
		return kmf;
	}

	private static Collection<? extends Certificate> parseCerts(byte[] pem)
			throws GeneralSecurityException {
		CertificateFactory cf = CertificateFactory.getInstance("X.509");
		Collection<? extends Certificate> certs = cf.generateCertificates(new ByteArrayInputStream(pem));
		if (certs.isEmpty()) {
			throw new AIServerException("PEM 안에 X.509 cert 없음");
		}
		// 최소 1개 X509 검증.
		certs.iterator().next().getClass().asSubclass(X509Certificate.class);
		return certs;
	}

	private static PrivateKey parsePkcs8Key(byte[] pem) throws GeneralSecurityException {
		String text = new String(pem, StandardCharsets.US_ASCII);
		String body = text
			.replace("-----BEGIN PRIVATE KEY-----", "")
			.replace("-----END PRIVATE KEY-----", "")
			.replaceAll("\\s+", "");
		if (body.isEmpty() || text.contains("BEGIN RSA PRIVATE KEY")) {
			throw new AIServerException(
				"PKCS#8 형식 (BEGIN PRIVATE KEY) 만 지원 — `openssl pkcs8 -topk8 -nocrypt -in src.key -out dst.key` 로 변환"
			);
		}
		byte[] der = Base64.getDecoder().decode(body);
		// 기본은 RSA. EC/Ed25519 도 PKCS#8 wrap 안에서 KeyFactory 가 알고리즘을 추론하지 못하므로
		// 학습 자료에선 RSA 로 고정 (gen_dev_certs.sh 도 RSA 산출).
		return KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(der));
	}
}
