package com.petfinect.api.service;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.domain.FamilyMember;
import com.petfinect.api.domain.User;
import com.petfinect.api.integration.kakao.KakaoOAuthClient;
import com.petfinect.api.integration.kakao.KakaoUser;
import com.petfinect.api.repository.FamilyMemberRepository;
import com.petfinect.api.repository.UserRepository;
import com.petfinect.api.security.JwtTokenProvider;
import com.petfinect.api.security.RefreshTokenStore;
import com.petfinect.api.web.dto.KakaoLoginResponse;
import com.petfinect.api.web.dto.TokenPair;
import com.petfinect.api.web.dto.UserSummary;
import com.petfinect.api.web.exception.ApiException;

/**
 * 인증 도메인 서비스 — Kakao 사용자 upsert + 토큰 페어 발급 + 회전.
 *
 * <h3>Spring 트랜잭션 패턴</h3>
 * <ul>
 *   <li>{@code @Transactional} — 메서드 진입 시 트랜잭션 열고, 정상 종료 시 commit, 예외 시 rollback.
 *       Python 의 explicit {@code await session.commit()} 와 달리 자동.</li>
 *   <li>읽기 전용 메서드는 {@code @Transactional(readOnly = true)} 로 hint — DB 가 read replica
 *       라우팅 등 최적화에 활용.</li>
 * </ul>
 *
 * <h3>upsert 패턴</h3>
 * <ul>
 *   <li>Python 은 {@code pg_insert(...).on_conflict_do_update(...)} 로 ON CONFLICT 사용.</li>
 *   <li>Java/JPA 는 ON CONFLICT 직접 매핑 어려움 → SELECT-then-INSERT/UPDATE 패턴.
 *       race 가능성은 있지만 카카오 ID 가 unique 라서 두 번째 트랜잭션이 IntegrityException → 재시도.
 *       학습 자료에선 단순 SELECT/UPDATE 로 충분.</li>
 * </ul>
 */
@Service
public class AuthService {

	private final UserRepository userRepository;
	private final FamilyMemberRepository familyMemberRepository;
	private final KakaoOAuthClient kakaoClient;
	private final JwtTokenProvider tokenProvider;
	private final RefreshTokenStore refreshStore;

	public AuthService(
		UserRepository userRepository,
		FamilyMemberRepository familyMemberRepository,
		KakaoOAuthClient kakaoClient,
		JwtTokenProvider tokenProvider,
		RefreshTokenStore refreshStore
	) {
		this.userRepository = userRepository;
		this.familyMemberRepository = familyMemberRepository;
		this.kakaoClient = kakaoClient;
		this.tokenProvider = tokenProvider;
		this.refreshStore = refreshStore;
	}

	@Transactional
	public KakaoLoginResponse loginWithKakao(String authCode, String redirectUri) {
		KakaoUser kakao = kakaoClient.exchangeCode(authCode, redirectUri);
		User user = upsertKakaoUser(kakao);
		String access = buildAccessFor(user);
		String refresh = refreshStore.issue(user.getId());
		return new KakaoLoginResponse(
			access,
			refresh,
			new UserSummary(user.getId(), user.getName(), user.getProfileImage())
		);
	}

	@Transactional
	public TokenPair refresh(String refreshToken) {
		Optional<RefreshTokenStore.RotationResult> rotated = refreshStore.rotate(refreshToken);
		if (rotated.isEmpty()) {
			throw new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "refresh token not found or expired");
		}
		User user = userRepository.findById(rotated.get().userId())
			.orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "user not found"));
		String access = buildAccessFor(user);
		return new TokenPair(access, rotated.get().newToken());
	}

	public void logout(String refreshToken) {
		// 멱등 — 없어도 OK.
		refreshStore.revoke(refreshToken);
	}

	@Transactional
	protected User upsertKakaoUser(KakaoUser kakao) {
		OffsetDateTime now = OffsetDateTime.now();
		User user = userRepository.findByKakaoId(kakao.kakaoId()).orElse(null);
		if (user == null) {
			user = User.builder()
				.kakaoId(kakao.kakaoId())
				.email(kakao.email())
				.name(kakao.name())
				.profileImage(kakao.profileImage())
				.lastLoginAt(now)
				.build();
		} else {
			user.setEmail(kakao.email());
			user.setName(kakao.name());
			user.setProfileImage(kakao.profileImage());
			user.setLastLoginAt(now);
		}
		return userRepository.save(user);
	}

	@Transactional(readOnly = true)
	protected String buildAccessFor(User user) {
		List<FamilyMember> memberships = familyMemberRepository.findByUserId(user.getId());
		List<UUID> fids = memberships.stream().map(FamilyMember::getFamilyId).toList();
		Map<UUID, String> roles = new HashMap<>();
		memberships.forEach(m -> roles.put(m.getFamilyId(), m.getRole().name()));
		return tokenProvider.encodeAccess(user.getId(), fids, roles);
	}
}
