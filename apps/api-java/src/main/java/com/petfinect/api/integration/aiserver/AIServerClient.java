package com.petfinect.api.integration.aiserver;

/**
 * AI 추론 서버 클라이언트 추상 — RTX 5090 로컬 GPU 서버 호출.
 *
 * <p>Python {@code AIServerClient Protocol} 와 1:1 contract.
 *
 * <h3>구현체</h3>
 * <ul>
 *   <li>{@link MockAIServerClient} — sha256 결정적 응답. 테스트/dev/CI.</li>
 *   <li>{@link RealAIServerClient} — Spring 6 RestClient + HMAC + mTLS. production.</li>
 * </ul>
 *
 * <h3>학습 포인트: blocking vs reactive</h3>
 * <ul>
 *   <li>Python 측은 {@code async def} — uvloop 위에서 동시 호출 친화.</li>
 *   <li>Java MVC + Spring Boot 4 + virtual threads → blocking 유지해도 동시성 손실 없음.</li>
 *   <li>비용/지연이 크다면 {@code WebClient} (Reactor) 로 전환 가능.</li>
 * </ul>
 */
public interface AIServerClient {

	/**
	 * @param imageBytes 원본 이미지 raw bytes
	 * @param region     {@code skin/eye/ear/gum} 중 하나
	 * @throws AIServerException 호출 실패 시
	 */
	VisionResult inferVision(byte[] imageBytes, String region);

	/**
	 * @param audioBytes 원본 오디오 raw bytes (wav/mp3/ogg 등)
	 * @throws AIServerException 호출 실패 시
	 */
	AudioResult inferAudio(byte[] audioBytes);
}
