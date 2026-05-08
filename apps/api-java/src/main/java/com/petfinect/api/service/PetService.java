package com.petfinect.api.service;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.domain.Family;
import com.petfinect.api.domain.FamilyMember;
import com.petfinect.api.domain.Pet;
import com.petfinect.api.domain.PetSpecies;
import com.petfinect.api.repository.FamilyMemberRepository;
import com.petfinect.api.repository.FamilyRepository;
import com.petfinect.api.repository.PetRepository;
import com.petfinect.api.web.exception.ApiException;

/**
 * Pet 도메인 서비스 — 생성/목록/조회.
 *
 * <h3>존재 누설 방지 정책</h3>
 * <p>{@link #getForUser(UUID, UUID)}: 펫이 없거나, 사용자가 그 펫의 family 멤버가 아니면
 * 모두 404 반환. 다른 가족의 펫 ID 를 추측해서 존재 여부를 알아내는 oracle 차단.
 * Python {@code get_pet_for_user} 와 동일.
 */
@Service
public class PetService {

	private final PetRepository petRepository;
	private final FamilyRepository familyRepository;
	private final FamilyMemberRepository familyMemberRepository;

	public PetService(
		PetRepository petRepository,
		FamilyRepository familyRepository,
		FamilyMemberRepository familyMemberRepository
	) {
		this.petRepository = petRepository;
		this.familyRepository = familyRepository;
		this.familyMemberRepository = familyMemberRepository;
	}

	@Transactional
	public Pet create(
		UUID familyId,
		String breed,
		LocalDate dob,
		Double weight,
		boolean neutered,
		List<String> conditions
	) {
		Family fam = familyRepository.findById(familyId)
			.orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "family not found"));

		Pet pet = Pet.builder()
			.family(fam)
			.species(PetSpecies.dog)
			.breed(breed)
			.dob(dob)
			.weight(weight)
			.neutered(neutered)
			.conditions(conditions == null ? List.of() : conditions)
			.build();
		return petRepository.save(pet);
	}

	@Transactional(readOnly = true)
	public List<Pet> listForFamily(UUID familyId) {
		return petRepository.findByFamilyId(familyId);
	}

	@Transactional(readOnly = true)
	public Pet getForUser(UUID petId, UUID userId) {
		Pet pet = petRepository.findById(petId)
			.orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "pet not found"));

		Optional<FamilyMember> membership = familyMemberRepository.findByFamilyIdAndUserId(
			pet.getFamily().getId(), userId
		);
		if (membership.isEmpty()) {
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "pet not found");
		}
		return pet;
	}
}
