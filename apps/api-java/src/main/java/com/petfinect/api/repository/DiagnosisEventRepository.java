package com.petfinect.api.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.DiagnosisEvent;

@Repository
public interface DiagnosisEventRepository extends JpaRepository<DiagnosisEvent, UUID> {

	List<DiagnosisEvent> findByPetIdOrderByCreatedAtDesc(UUID petId, Pageable pageable);
}
