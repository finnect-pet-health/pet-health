package com.petfinect.api.service;

import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.domain.User;
import com.petfinect.api.repository.FamilyMemberRepository;
import com.petfinect.api.repository.FamilyRepository;
import com.petfinect.api.repository.UserRepository;
import com.petfinect.api.web.dto.FamilySummary;
import com.petfinect.api.web.dto.MeResponse;
import com.petfinect.api.web.exception.ApiException;

/**
 * 현재 사용자 + 소속 가족 목록 조회.
 *
 * <h3>JPA 쿼리 단순화 결정</h3>
 * <p>Python 은 GROUP BY + JOIN subquery 한 방으로 처리. JPA/JPQL 로 옮기면 복잡해지므로
 * 학습 자료에선 N+1 가능성을 감수하고 두 단계 (memberships → families) 로 분리.
 * 운영 트래픽 늘면 native query 또는 {@code @Query} JPQL 로 최적화.
 */
@Service
public class MeService {

	private final UserRepository userRepository;
	private final FamilyMemberRepository familyMemberRepository;
	private final FamilyRepository familyRepository;

	public MeService(
		UserRepository userRepository,
		FamilyMemberRepository familyMemberRepository,
		FamilyRepository familyRepository
	) {
		this.userRepository = userRepository;
		this.familyMemberRepository = familyMemberRepository;
		this.familyRepository = familyRepository;
	}

	@Transactional(readOnly = true)
	public MeResponse loadMe(UUID userId) {
		User user = userRepository.findById(userId)
			.orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "user not found"));

		List<FamilySummary> families = familyMemberRepository.findByUserId(userId).stream()
			.map(m -> {
				int memberCount = familyMemberRepository.findByFamilyId(m.getFamilyId()).size();
				String name = familyRepository.findById(m.getFamilyId())
					.map(f -> f.getName())
					.orElse("");
				return new FamilySummary(m.getFamilyId(), name, m.getRole().name(), memberCount);
			})
			.toList();

		return new MeResponse(user.getId(), user.getName(), user.getProfileImage(), families);
	}
}
