package com.petfinect.api.integration.aiserver;

import java.io.IOException;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.UUID;

import javax.net.ssl.SSLContext;

import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

/**
 * 실 AI 서버 호출 클라이언트 — Spring 6 {@link RestClient} + 선택적 mTLS + HMAC 헤더.
 *
 * <p>현재는 Phase 8 진단 라우터 합류 전이라 실 운영 트래픽 없음. {@link MockAIServerClient} 가
 * 기본 빈이며, {@code petfinect.ai-server.use-mock=false} 일 때만 본 구현이 등록.
 *
 * <h3>Spring 6 RestClient + JdkClientHttpRequestFactory</h3>
 * <ul>
 *   <li>{@link HttpClient} (java.net) 가 SSLContext 직접 지원 — Apache HttpClient/OkHttp 의존성 제거.</li>
 *   <li>{@link JdkClientHttpRequestFactory} 로 RestClient 와 연결.</li>
 *   <li>학습 포인트: Python httpx 의 {@code AsyncClient(verify=ctx, cert=...)} 를 Java 진영의
 *       표준 라이브러리만으로 동등 구현.</li>
 * </ul>
 *
 * <h3>Multipart 전송</h3>
 * <ul>
 *   <li>AI 서버 라우트 ({@code /infer/vision, /infer/audio}) 는 multipart/form-data 수신 + raw bytes 에 대해 HMAC 검증.</li>
 *   <li>HMAC 입력은 multipart 봉투가 아니라 <b>업로드 파일 raw bytes</b> 자체. 헤더로 hex digest 송부.</li>
 * </ul>
 */
public class RealAIServerClient implements AIServerClient {

	private static final String HMAC_HEADER = "X-AI-HMAC";

	private final RestClient restClient;
	private final HmacSigner hmac;

	public RealAIServerClient(String baseUrl, String sharedSecret, SSLContext sslContext) {
		this.hmac = new HmacSigner(sharedSecret);

		HttpClient.Builder httpBuilder = HttpClient.newBuilder()
			.connectTimeout(Duration.ofSeconds(5));
		if (sslContext != null) {
			httpBuilder.sslContext(sslContext);
		}
		HttpClient httpClient = httpBuilder.build();

		this.restClient = RestClient.builder()
			.baseUrl(baseUrl)
			.requestFactory(new JdkClientHttpRequestFactory(httpClient))
			.build();
	}

	@Override
	public VisionResult inferVision(byte[] imageBytes, String region) {
		String boundary = "----HpBoundary" + UUID.randomUUID().toString().replace("-", "");
		byte[] body = buildVisionMultipart(boundary, imageBytes, region);
		String signature = hmac.signHex(imageBytes);

		try {
			VisionResult result = restClient.post()
				.uri("/infer/vision")
				.contentType(MediaType.parseMediaType("multipart/form-data; boundary=" + boundary))
				.header(HMAC_HEADER, signature)
				.body(body)
				.retrieve()
				.onStatus(HttpStatusCode::isError, (req, resp) -> {
					throw new AIServerException("infer/vision " + resp.getStatusCode().value());
				})
				.body(VisionResult.class);
			if (result == null) {
				throw new AIServerException("infer/vision empty body");
			}
			return result;
		} catch (RestClientResponseException e) {
			throw new AIServerException("infer/vision " + e.getStatusCode().value(), e);
		}
	}

	@Override
	public AudioResult inferAudio(byte[] audioBytes) {
		String boundary = "----HpBoundary" + UUID.randomUUID().toString().replace("-", "");
		byte[] body = buildAudioMultipart(boundary, audioBytes);
		String signature = hmac.signHex(audioBytes);

		try {
			AudioResult result = restClient.post()
				.uri("/infer/audio")
				.contentType(MediaType.parseMediaType("multipart/form-data; boundary=" + boundary))
				.header(HMAC_HEADER, signature)
				.body(body)
				.retrieve()
				.onStatus(HttpStatusCode::isError, (req, resp) -> {
					throw new AIServerException("infer/audio " + resp.getStatusCode().value());
				})
				.body(AudioResult.class);
			if (result == null) {
				throw new AIServerException("infer/audio empty body");
			}
			return result;
		} catch (RestClientResponseException e) {
			throw new AIServerException("infer/audio " + e.getStatusCode().value(), e);
		}
	}

	// === multipart 직접 빌드 ===
	// Spring 의 MultipartBodyBuilder 도 가능하나, 학습용으로 raw 와이어 포맷을 명시.

	static byte[] buildVisionMultipart(String boundary, byte[] image, String region) {
		try (var out = new java.io.ByteArrayOutputStream()) {
			writePart(out, boundary, "file", "image.bin", "application/octet-stream", image);
			writeField(out, boundary, "region", region);
			out.write(("--" + boundary + "--\r\n").getBytes(StandardCharsets.US_ASCII));
			return out.toByteArray();
		} catch (IOException e) {
			throw new AIServerException("multipart 빌드 실패", e);
		}
	}

	static byte[] buildAudioMultipart(String boundary, byte[] audio) {
		try (var out = new java.io.ByteArrayOutputStream()) {
			writePart(out, boundary, "file", "audio.bin", "application/octet-stream", audio);
			out.write(("--" + boundary + "--\r\n").getBytes(StandardCharsets.US_ASCII));
			return out.toByteArray();
		} catch (IOException e) {
			throw new AIServerException("multipart 빌드 실패", e);
		}
	}

	private static void writePart(
		java.io.ByteArrayOutputStream out, String boundary,
		String name, String filename, String contentType, byte[] data
	) throws IOException {
		StringBuilder header = new StringBuilder();
		header.append("--").append(boundary).append("\r\n");
		header.append("Content-Disposition: form-data; name=\"").append(name)
			.append("\"; filename=\"").append(filename).append("\"\r\n");
		header.append("Content-Type: ").append(contentType).append("\r\n\r\n");
		out.write(header.toString().getBytes(StandardCharsets.US_ASCII));
		out.write(data);
		out.write("\r\n".getBytes(StandardCharsets.US_ASCII));
	}

	private static void writeField(
		java.io.ByteArrayOutputStream out, String boundary, String name, String value
	) throws IOException {
		StringBuilder header = new StringBuilder();
		header.append("--").append(boundary).append("\r\n");
		header.append("Content-Disposition: form-data; name=\"").append(name).append("\"\r\n\r\n");
		header.append(value);
		header.append("\r\n");
		out.write(header.toString().getBytes(StandardCharsets.UTF_8));
	}
}
