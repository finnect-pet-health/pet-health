package com.petfinect.api.integration.aiserver;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicReference;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/**
 * RealAIServerClient — HMAC 헤더 + multipart 봉투 + JSON 응답 파싱 검증.
 *
 * <p>실 mTLS handshake 는 dev cert 가 commit 안 돼있으므로 plain HTTP 로 검증. mTLS 분기
 * (SSLContext null vs 주입) 는 {@link MtlsSslContextFactoryTest} 에서 별도 커버.
 *
 * <h3>왜 testcontainers 가 아닌 in-process HttpServer 인가</h3>
 * <ul>
 *   <li>AI 서버 자체는 별 의존 (Python torch + transformers) — 도커 부팅 무거움.</li>
 *   <li>JDK 내장 {@link HttpServer} 로 와이어 프로토콜만 검증 → 빠름 + 결정적.</li>
 * </ul>
 */
class RealAIServerClientHttpTest {

	private HttpServer server;
	private String baseUrl;
	private final AtomicReference<String> lastHmacHeader = new AtomicReference<>();
	private final AtomicReference<byte[]> lastBody = new AtomicReference<>();

	@BeforeEach
	void start() throws IOException {
		server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
		server.createContext("/infer/vision", this::handleVision);
		server.createContext("/infer/audio", this::handleAudio);
		server.start();
		baseUrl = "http://127.0.0.1:" + server.getAddress().getPort();
	}

	@AfterEach
	void stop() {
		if (server != null) {
			server.stop(0);
		}
	}

	@Test
	void inferVision_sendsHmacAndParsesResponse() {
		RealAIServerClient client = new RealAIServerClient(baseUrl, "test-secret", null);
		byte[] image = "fake-image-bytes".getBytes(StandardCharsets.UTF_8);

		VisionResult result = client.inferVision(image, "skin");

		String expectedHmac = new HmacSigner("test-secret").signHex(image);
		assertThat(lastHmacHeader.get()).isEqualTo(expectedHmac);
		assertThat(new String(lastBody.get(), StandardCharsets.UTF_8))
			.contains("name=\"file\"")
			.contains("name=\"region\"")
			.contains("skin");
		assertThat(result.topResults()).hasSize(1);
		assertThat(result.topResults().get(0).label()).isEqualTo("skin_redness");
		assertThat(result.confidenceTop1()).isEqualTo(0.9);
	}

	@Test
	void inferAudio_sendsHmacAndParsesResponse() {
		RealAIServerClient client = new RealAIServerClient(baseUrl, "test-secret", null);
		byte[] audio = "fake-audio-bytes".getBytes(StandardCharsets.UTF_8);

		AudioResult result = client.inferAudio(audio);

		String expectedHmac = new HmacSigner("test-secret").signHex(audio);
		assertThat(lastHmacHeader.get()).isEqualTo(expectedHmac);
		assertThat(result.category()).isEqualTo("기침");
		assertThat(result.confidenceTop1()).isEqualTo(0.6);
	}

	@Test
	void infer_serverError_throwsAIServerException() throws IOException {
		HttpServer broken = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
		broken.createContext("/infer/vision", ex -> {
			ex.sendResponseHeaders(500, -1);
			ex.close();
		});
		broken.start();
		try {
			String url = "http://127.0.0.1:" + broken.getAddress().getPort();
			RealAIServerClient client = new RealAIServerClient(url, "s", null);
			assertThatThrownBy(() -> client.inferVision(new byte[]{1, 2, 3}, "skin"))
				.isInstanceOf(AIServerException.class)
				.hasMessageContaining("500");
		} finally {
			broken.stop(0);
		}
	}

	private void handleVision(HttpExchange ex) throws IOException {
		captureRequest(ex);
		String json = """
			{
			  "top_results": [{"label": "skin_redness", "score": 0.9}],
			  "action": "immediate",
			  "confidence_top1": 0.9
			}
			""";
		writeJson(ex, json);
	}

	private void handleAudio(HttpExchange ex) throws IOException {
		captureRequest(ex);
		String json = """
			{
			  "category": "기침",
			  "score": 0.6,
			  "action": "schedule",
			  "confidence_top1": 0.6
			}
			""";
		writeJson(ex, json);
	}

	private void captureRequest(HttpExchange ex) throws IOException {
		lastHmacHeader.set(ex.getRequestHeaders().getFirst("X-AI-HMAC"));
		lastBody.set(ex.getRequestBody().readAllBytes());
	}

	private void writeJson(HttpExchange ex, String json) throws IOException {
		byte[] payload = json.getBytes(StandardCharsets.UTF_8);
		ex.getResponseHeaders().add("Content-Type", "application/json");
		ex.sendResponseHeaders(200, payload.length);
		try (OutputStream out = ex.getResponseBody()) {
			out.write(payload);
		}
	}
}
