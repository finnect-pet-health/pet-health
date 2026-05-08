package com.petfinect.api.integration.kakao;

/**
 * 카카오 auth_code 교환 실패 시 던지는 도메인 예외.
 *
 * <p>{@link RuntimeException} 상속 → JPA/Spring 에서 transaction rollback 자동 트리거.
 * Checked exception 으로 만들면 호출 체인 전체에 {@code throws} 를 강제하므로,
 * Spring 관례상 unchecked exception 사용.
 */
public class KakaoExchangeException extends RuntimeException {
	public KakaoExchangeException(String message) {
		super(message);
	}

	public KakaoExchangeException(String message, Throwable cause) {
		super(message, cause);
	}
}
