package com.petfinect.api.service;

import java.time.OffsetDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.domain.Family;
import com.petfinect.api.domain.FamilyMember;
import com.petfinect.api.domain.MemberRole;
import com.petfinect.api.domain.User;
import com.petfinect.api.repository.FamilyMemberRepository;
import com.petfinect.api.repository.FamilyRepository;
import com.petfinect.api.repository.UserRepository;
import com.petfinect.api.web.exception.ApiException;

/**
 * Family 도메인 서비스 — 생성/조회/초대/가입/멤버.
 *
 * <h3>Python 대응</h3>
 * <ul>
 *   <li>{@code create_family_with_owner}: Family + 본인 owner FamilyMember row 동일 트랜잭션</li>
 *   <li>{@code issue_invite}: 8자 base32, IntegrityException 시 1회 재시도</li>
 *   <li>{@code join_by_code}: 만료 검증, 이미 멤버 검증, member role 로 가입</li>
 *   <li>{@code list_my_families}, {@code list_members}: 조회</li>
 * </ul>
 */
@Service
public class FamilyService {

	private final FamilyRepository familyRepository;
	private final FamilyMemberRepository familyMemberRepository;
	private final UserRepository userRepository;
	private final InviteCodeGenerator inviteCodeGenerator;

	public FamilyService(
		FamilyRepository familyRepository,
		FamilyMemberRepository familyMemberRepository,
		UserRepository userRepository,
		InviteCodeGenerator inviteCodeGenerator
	) {
		this.familyRepository = familyRepository;
		this.familyMemberRepository = familyMemberRepository;
		this.userRepository = userRepository;
		this.inviteCodeGenerator = inviteCodeGenerator;
	}

	@Transactional
	public Family createWithOwner(UUID userId, String name) {
		User owner = userRepository.findById(userId)
			.orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "user not found"));

		Family fam = Family.builder()
			.name(name)
			.owner(owner)
			.build();
		fam = familyRepository.save(fam);

		FamilyMember membership = FamilyMember.builder()
			.familyId(fam.getId())
			.userId(owner.getId())
			.family(fam)
			.user(owner)
			.role(MemberRole.owner)
			.build();
		familyMemberRepository.save(membership);

		return fam;
	}

	@Transactional(readOnly = true)
	public List<FamilyListItem> listMyFamilies(UUID userId) {
		List<FamilyMember> memberships = familyMemberRepository.findByUserId(userId);
		return memberships.stream()
			.map(m -> {
				Family fam = familyRepository.findById(m.getFamilyId())
					.orElseThrow(() -> new IllegalStateException("orphan FamilyMember row"));
				int memberCount = familyMemberRepository.findByFamilyId(m.getFamilyId()).size();
				return new FamilyListItem(fam.getId(), fam.getName(), m.getRole().name(), memberCount);
			})
			.toList();
	}

	@Transactional
	public InviteResult issueInvite(UUID familyId, int ttlHours) {
		Family fam = familyRepository.findById(familyId)
			.orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "family not found"));

		OffsetDateTime expiresAt = OffsetDateTime.now().plusHours(ttlHours);
		// 충돌 시 1회 재시도 (Python 과 동일 정책).
		for (int attempt = 0; attempt < 2; attempt++) {
			String code = inviteCodeGenerator.generate();
			fam.setInviteCode(code);
			fam.setInviteExpiresAt(expiresAt);
			try {
				familyRepository.saveAndFlush(fam);
				return new InviteResult(code, expiresAt);
			} catch (DataIntegrityViolationException ignore) {
				// 다시 생성 시도
			}
		}
		throw new ApiException(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL", "failed to generate unique invite code");
	}

	@Transactional
	public Family joinByCode(UUID userId, String inviteCode) {
		Family fam = familyRepository.findByInviteCode(inviteCode)
			.orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "invite code not found"));

		OffsetDateTime now = OffsetDateTime.now();
		if (fam.getInviteExpiresAt() == null || fam.getInviteExpiresAt().isBefore(now)) {
			throw new ApiException(HttpStatus.GONE, "INVITE_EXPIRED", "invite code expired");
		}

		if (familyMemberRepository.existsByFamilyIdAndUserId(fam.getId(), userId)) {
			throw new ApiException(HttpStatus.CONFLICT, "ALREADY_MEMBER", "already a member of this family");
		}

		User user = userRepository.findById(userId)
			.orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "user not found"));

		FamilyMember membership = FamilyMember.builder()
			.familyId(fam.getId())
			.userId(user.getId())
			.family(fam)
			.user(user)
			.role(MemberRole.member)
			.build();
		familyMemberRepository.save(membership);
		return fam;
	}

	@Transactional(readOnly = true)
	public List<MemberDetail> listMembers(UUID familyId) {
		List<FamilyMember> members = familyMemberRepository.findByFamilyId(familyId);
		// 사용자 정보 한 번에 매핑 — N+1 가능성 있지만 학습 자료에선 명시적이 우선.
		Map<UUID, User> userMap = new HashMap<>();
		userRepository.findAllById(members.stream().map(FamilyMember::getUserId).toList())
			.forEach(u -> userMap.put(u.getId(), u));

		return members.stream()
			.sorted((a, b) -> a.getJoinedAt().compareTo(b.getJoinedAt()))
			.map(m -> new MemberDetail(
				m.getUserId(),
				userMap.containsKey(m.getUserId()) ? userMap.get(m.getUserId()).getName() : "",
				m.getRole().name(),
				m.getJoinedAt()
			))
			.toList();
	}

	public record FamilyListItem(UUID id, String name, String role, int memberCount) {}
	public record InviteResult(String inviteCode, OffsetDateTime expiresAt) {}
	public record MemberDetail(UUID userId, String name, String role, OffsetDateTime joinedAt) {}
}
