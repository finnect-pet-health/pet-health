package com.petfinect.api.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.FamilyInvite;

@Repository
public interface FamilyInviteRepository extends JpaRepository<FamilyInvite, UUID> {

	Optional<FamilyInvite> findByCode(String code);
}
