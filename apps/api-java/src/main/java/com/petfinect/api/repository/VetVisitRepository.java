package com.petfinect.api.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.VetVisit;

@Repository
public interface VetVisitRepository extends JpaRepository<VetVisit, UUID> {

	List<VetVisit> findByPetIdOrderByVisitedAtDesc(UUID petId);
}
