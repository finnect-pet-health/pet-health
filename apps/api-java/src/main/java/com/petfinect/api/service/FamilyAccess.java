package com.petfinect.api.service;

import java.util.Optional;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.domain.FamilyMember;
import com.petfinect.api.domain.MemberRole;
import com.petfinect.api.repository.FamilyMemberRepository;
import com.petfinect.api.security.AccessClaims;
import com.petfinect.api.web.exception.ApiException;

/**
 * Family RBAC 접근 제어 — Python {@code require_family} 데코레이터의 Java 버전.
 *
 * <h3>정책 (Python {@code app.security.deps.require_family} 와 동일)</h3>
 * <ol>
 *   <li>Token 의 {@code roles} 맵을 먼저 본다 (fast path).</li>
 *   <li>DB 의 {@link FamilyMember} 도 조회 (방금 가입한 family 는 토큰에 없을 수 있음).</li>
 *   <li>DB 에 없는데 토큰에 있다 → 403 FORBIDDEN (토큰이 stale).</li>
 *   <li>DB 에도 토큰에도 없다 → 404 NOT_FOUND (펫과 동일하게 존재 사실 누설 방지).</li>
 *   <li>{@code requiredRole=owner} 인데 effective role 이 owner 가 아님 → 403.</li>
 * </ol>
 *
 * <h3>왜 별도 빈으로 추출했나</h3>
 * <ul>
 *   <li>Python 은 {@code Depends(require_family("owner"))} 로 데코레이터 주입.</li>
 *   <li>Java 는 동일 패턴이 어색 → 컨트롤러에서 명시적으로 호출하는 서비스로 추출.</li>
 *   <li>대안: Spring Security {@code @PreAuthorize("@familyAccess.checkOwner(...)")} SpEL.
 *       학습 자료에선 명시적 호출이 흐름 추적에 유리.</li>
 * </ul>
 */
@Service
public class FamilyAccess {

	private final FamilyMemberRepository familyMemberRepository;

	public FamilyAccess(FamilyMemberRepository familyMemberRepository) {
		this.familyMemberRepository = familyMemberRepository;
	}

	@Transactional(readOnly = true)
	public FamilyMember requireMember(UUID familyId, AccessClaims claims) {
		return require(familyId, claims, MemberRole.member);
	}

	@Transactional(readOnly = true)
	public FamilyMember requireOwner(UUID familyId, AccessClaims claims) {
		return require(familyId, claims, MemberRole.owner);
	}

	private FamilyMember require(UUID familyId, AccessClaims claims, MemberRole required) {
		String tokenRole = claims.roles().get(familyId);

		Optional<FamilyMember> membershipOpt = familyMemberRepository.findByFamilyIdAndUserId(
			familyId, claims.sub()
		);

		if (membershipOpt.isEmpty()) {
			if (tokenRole != null) {
				throw new ApiException(HttpStatus.FORBIDDEN, "FORBIDDEN", "not a member of this family");
			}
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "family not found");
		}

		FamilyMember member = membershipOpt.get();
		if (required == MemberRole.owner && member.getRole() != MemberRole.owner) {
			throw new ApiException(HttpStatus.FORBIDDEN, "FORBIDDEN", "owner role required");
		}
		return member;
	}
}
