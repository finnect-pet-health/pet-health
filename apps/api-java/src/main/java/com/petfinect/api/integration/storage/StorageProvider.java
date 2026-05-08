package com.petfinect.api.integration.storage;

/**
 * 객체 저장소 추상.
 *
 * <h3>contract (Python {@code StorageProvider Protocol} 동일)</h3>
 * <ul>
 *   <li>{@code presignPut} — 클라이언트가 직접 PUT 할 URL 발급</li>
 *   <li>{@code presignGet} — 다운로드 URL 발급</li>
 *   <li>{@code putBytes} — 서버 측 직접 업로드 (mock raw upload 등)</li>
 *   <li>{@code fetchBytes} — 서버 측 다운로드 (AI server 호출 시 등)</li>
 * </ul>
 *
 * <h3>학습 포인트: blocking ↔ async</h3>
 * <ul>
 *   <li>Python 은 async (aiobotocore). Java MVC 는 blocking — Spring Boot 4 에선
 *       virtual threads 로 동시성 확보 (서블릿 컨테이너 옵션).</li>
 *   <li>네트워크 I/O 가 많은 storage 는 reactive 도 가능하지만 학습 자료에선 blocking 이 명료.</li>
 * </ul>
 */
public interface StorageProvider {

	String presignPut(String key, String contentType, int ttlSeconds);

	String presignGet(String key, int ttlSeconds);

	byte[] fetchBytes(String key);

	void putBytes(String key, byte[] data, String contentType);
}
