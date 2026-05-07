package com.petfinect.api.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.FamilyMember;
import com.petfinect.api.domain.FamilyMemberId;

/**
 * Composite PK 사용 — {@code <FamilyMember, FamilyMemberId>} 시그니처.
 * findById 호출 시 {@code new FamilyMemberId(familyId, userId)} 전달.
 */
@Repository
public interface FamilyMemberRepository extends JpaRepository<FamilyMember, FamilyMemberId> {

	List<FamilyMember> findByUserId(UUID userId);

	List<FamilyMember> findByFamilyId(UUID familyId);

	Optional<FamilyMember> findByFamilyIdAndUserId(UUID familyId, UUID userId);

	boolean existsByFamilyIdAndUserId(UUID familyId, UUID userId);
}
