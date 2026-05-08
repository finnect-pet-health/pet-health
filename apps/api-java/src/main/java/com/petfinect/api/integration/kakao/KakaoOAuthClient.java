package com.petfinect.api.integration.kakao;

/**
 * 카카오 OAuth 클라이언트 인터페이스.
 *
 * <h3>Python {@code Protocol} ↔ Java {@code interface}</h3>
 * <ul>
 *   <li>Python 의 {@code typing.Protocol} 은 duck typing — 메서드 시그니처만 일치하면 OK.</li>
 *   <li>Java 의 {@code interface} 는 명시적 implements 필요. 컴파일러가 검증.</li>
 *   <li>학습 포인트: Java 의 인터페이스가 Python 보다 엄격하지만, IDE 의 자동완성/리팩토링이
 *       훨씬 안전. {@link KakaoOAuthClient} 한 곳만 바꿔도 모든 구현체가 즉시 컴파일 에러로 알림.</li>
 * </ul>
 */
public interface KakaoOAuthClient {
	/**
	 * 카카오 auth_code 를 사용자 프로필로 교환.
	 *
	 * @throws KakaoExchangeException auth_code 가 무효하거나 카카오 API 가 실패한 경우
	 */
	KakaoUser exchangeCode(String code, String redirectUri);
}
