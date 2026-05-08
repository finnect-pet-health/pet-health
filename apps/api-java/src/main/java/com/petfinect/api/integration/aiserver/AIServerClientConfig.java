package com.petfinect.api.integration.aiserver;

import java.nio.file.Path;

import javax.net.ssl.SSLContext;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * {@link AIServerClient} 빈 분기 — mock(default) ↔ real(HMAC + optional mTLS).
 *
 * <h3>활성화</h3>
 * <ul>
 *   <li>기본 ({@code petfinect.ai-server.use-mock=true} 또는 미설정) → {@link MockAIServerClient}.</li>
 *   <li>{@code petfinect.ai-server.use-mock=false} → {@link RealAIServerClient}.
 *       PEM 경로 셋팅 시 mTLS, 미설정 시 plain HTTP/HTTPS 만.</li>
 * </ul>
 *
 * <h3>학습 포인트: {@link ConditionalOnProperty}</h3>
 * <ul>
 *   <li>Spring Boot 의 conditional bean — 환경변수/프로퍼티 기반 자동 wiring.</li>
 *   <li>{@code matchIfMissing = true} → 프로퍼티 미설정 시 mock 이 기본 (Python factory 의
 *       {@code os.getenv("AI_SERVER_USE_MOCK", "")} 과 같은 의도).</li>
 *   <li>대안: Phase 3/6 에서 사용한 {@code @Profile} 분기. 환경 단위 swap 에는 profile 이,
 *       토글 단위 swap 에는 conditional 이 더 적합.</li>
 * </ul>
 */
@Configuration
public class AIServerClientConfig {

	@Bean
	@ConditionalOnProperty(name = "petfinect.ai-server.use-mock", havingValue = "true", matchIfMissing = true)
	public AIServerClient mockAIServerClient() {
		return new MockAIServerClient();
	}

	@Bean
	@ConditionalOnProperty(name = "petfinect.ai-server.use-mock", havingValue = "false")
	public AIServerClient realAIServerClient(
		@Value("${petfinect.ai-server.base-url}") String baseUrl,
		@Value("${petfinect.ai-server.shared-secret}") String sharedSecret,
		@Value("${petfinect.ai-server.mtls.ca-cert:}") String caCert,
		@Value("${petfinect.ai-server.mtls.client-cert:}") String clientCert,
		@Value("${petfinect.ai-server.mtls.client-key:}") String clientKey
	) {
		SSLContext sslContext = buildSslContext(caCert, clientCert, clientKey);
		return new RealAIServerClient(baseUrl, sharedSecret, sslContext);
	}

	private static SSLContext buildSslContext(String caCert, String clientCert, String clientKey) {
		boolean hasClient = !clientCert.isEmpty() && !clientKey.isEmpty();
		boolean hasCa = !caCert.isEmpty();

		if (!hasCa && !hasClient) {
			return null;  // plain HTTP/HTTPS — JDK 기본 trust store.
		}
		if (!hasCa) {
			throw new IllegalStateException(
				"client cert/key 셋팅됐는데 ca-cert 미설정 — 서버 검증 불가"
			);
		}
		if (hasClient) {
			return MtlsSslContextFactory.build(
				Path.of(caCert), Path.of(clientCert), Path.of(clientKey)
			);
		}
		return MtlsSslContextFactory.buildTrustOnly(Path.of(caCert));
	}
}
