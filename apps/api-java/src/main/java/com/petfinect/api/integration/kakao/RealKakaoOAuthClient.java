package com.petfinect.api.integration.kakao;

import java.util.Map;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

/**
 * 카카오 실제 OAuth 클라이언트 (W2 본구현).
 *
 * <h3>Spring 6 의 {@link RestClient}</h3>
 * <ul>
 *   <li>RestTemplate 의 후속 — synchronous, fluent. Python 의 httpx 와 비슷한 사용감.</li>
 *   <li>비동기 필요시 {@code WebClient} (reactive) 사용. 본 프로젝트는 traditional MVC 라
 *       blocking RestClient 가 적합.</li>
 * </ul>
 *
 * <p>Step 1: auth_code → kakao access_token 교환<br>
 * Step 2: kakao access_token → 사용자 정보 조회<br>
 * Step 3: KakaoUser DTO 로 변환
 */
public class RealKakaoOAuthClient implements KakaoOAuthClient {

	private static final String TOKEN_URL = "https://kauth.kakao.com/oauth/token";
	private static final String USERINFO_URL = "https://kapi.kakao.com/v2/user/me";

	private final RestClient restClient;
	private final String restApiKey;
	private final String clientSecret;

	public RealKakaoOAuthClient(String restApiKey, String clientSecret) {
		this.restClient = RestClient.create();
		this.restApiKey = restApiKey;
		this.clientSecret = clientSecret;
	}

	@Override
	@SuppressWarnings("unchecked")
	public KakaoUser exchangeCode(String code, String redirectUri) {
		MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
		form.add("grant_type", "authorization_code");
		form.add("client_id", restApiKey);
		form.add("client_secret", clientSecret);
		form.add("redirect_uri", redirectUri);
		form.add("code", code);

		Map<String, Object> tokenResp = restClient.post()
			.uri(TOKEN_URL)
			.contentType(MediaType.APPLICATION_FORM_URLENCODED)
			.body(form)
			.retrieve()
			.onStatus(HttpStatusCode::isError, (req, resp) -> {
				throw new KakaoExchangeException("token_exchange_failed: " + resp.getStatusCode().value());
			})
			.body(Map.class);

		if (tokenResp == null) {
			throw new KakaoExchangeException("empty_token_response");
		}
		String kakaoAccessToken = (String) tokenResp.get("access_token");

		Map<String, Object> userResp = restClient.get()
			.uri(USERINFO_URL)
			.header(HttpHeaders.AUTHORIZATION, "Bearer " + kakaoAccessToken)
			.retrieve()
			.body(Map.class);

		if (userResp == null) {
			throw new KakaoExchangeException("empty_userinfo_response");
		}

		String kakaoId = String.valueOf(userResp.get("id"));
		Map<String, Object> kakaoAccount = (Map<String, Object>) userResp.get("kakao_account");
		Map<String, Object> profile = kakaoAccount != null
			? (Map<String, Object>) kakaoAccount.get("profile")
			: null;

		String name = profile != null ? (String) profile.getOrDefault("nickname", "") : "";
		String email = kakaoAccount != null ? (String) kakaoAccount.get("email") : null;
		String profileImage = profile != null ? (String) profile.get("profile_image_url") : null;

		return new KakaoUser(kakaoId, name, email, profileImage);
	}
}
