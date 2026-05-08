package com.petfinect.api.integration.aiserver;

/**
 * AI 서버 호출 실패 — timeout, HMAC 불일치, mTLS handshake 실패, 5xx 응답.
 *
 * <p>Python {@code AIServerError} 와 동일 의도. 라우터(Phase 8) 는 본 예외를 catch 하여
 * 룰 기반 fallback 응답을 200 으로 반환할지, 502 로 노출할지 결정.
 *
 * <h3>학습 포인트: checked vs unchecked</h3>
 * <ul>
 *   <li>{@code RuntimeException} 상속 → unchecked (try/catch 강제 X).</li>
 *   <li>학습 자료에서는 boilerplate 회피를 위해 unchecked 가 일반적.</li>
 *   <li>대안: {@code Exception} 직접 상속하면 checked — 호출부가 try/catch 강제, 흐름 명시화.</li>
 * </ul>
 */
public class AIServerException extends RuntimeException {

	public AIServerException(String message) {
		super(message);
	}

	public AIServerException(String message, Throwable cause) {
		super(message, cause);
	}
}
