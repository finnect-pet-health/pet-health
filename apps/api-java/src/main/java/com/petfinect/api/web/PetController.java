package com.petfinect.api.web;

import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.petfinect.api.domain.Pet;
import com.petfinect.api.security.JwtAuthenticationFilter.AuthenticatedUser;
import com.petfinect.api.service.FamilyAccess;
import com.petfinect.api.service.PetService;
import com.petfinect.api.web.dto.PetCreateRequest;
import com.petfinect.api.web.dto.PetResponse;
import com.petfinect.api.web.exception.ApiException;

import jakarta.validation.Valid;

/**
 * Pet 라우트 — Python {@code apps/api/app/api/v1/pets.py} 와 contract 동일.
 *
 * <h3>두 라우트가 분리된 이유</h3>
 * <ul>
 *   <li>{@code /v1/families/{familyId}/pets} — family 권한 검사 후 펫 작업 (생성/목록).</li>
 *   <li>{@code /v1/pets/{petId}} — 직접 조회. 펫의 family 멤버십을 별도 검증.</li>
 *   <li>한 컨트롤러에 둘 다 두면 라우팅 prefix 가 달라 {@link RequestMapping} 충돌.
 *       Spring 은 한 클래스에 여러 base path 를 막지 않지만 가독성 문제 →
 *       Python 은 두 router 분리, Java 도 두 controller 또는 한 controller + 두 메서드 set.
 *       학습 자료에선 한 컨트롤러로 합치되 {@link RequestMapping} 없이 메서드별 fully-qualified path.</li>
 * </ul>
 */
@RestController
@RequestMapping("")
public class PetController {

	private final PetService petService;
	private final FamilyAccess familyAccess;

	public PetController(PetService petService, FamilyAccess familyAccess) {
		this.petService = petService;
		this.familyAccess = familyAccess;
	}

	@PostMapping("/v1/families/{family_id}/pets")
	public PetResponse createInFamily(
		@PathVariable("family_id") String familyId,
		@Valid @RequestBody PetCreateRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		UUID fid = parseUuidOr404(familyId, "family");
		familyAccess.requireOwner(fid, principal.claims());
		Pet pet = petService.create(
			fid,
			req.breed(),
			req.dob(),
			req.weight(),
			req.neutered() != null ? req.neutered() : false,
			req.conditions()
		);
		return serialize(pet);
	}

	@GetMapping("/v1/families/{family_id}/pets")
	public List<PetResponse> listInFamily(
		@PathVariable("family_id") String familyId,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		UUID fid = parseUuidOr404(familyId, "family");
		familyAccess.requireMember(fid, principal.claims());
		return petService.listForFamily(fid).stream().map(this::serialize).toList();
	}

	@GetMapping("/v1/pets/{pet_id}")
	public PetResponse get(
		@PathVariable("pet_id") String petId,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		UUID pid = parseUuidOr404(petId, "pet");
		Pet pet = petService.getForUser(pid, principal.claims().sub());
		return serialize(pet);
	}

	private PetResponse serialize(Pet pet) {
		return new PetResponse(
			pet.getId(),
			pet.getFamily().getId(),
			pet.getSpecies().name(),
			pet.getBreed(),
			pet.getDob(),
			pet.getWeight(),
			Boolean.TRUE.equals(pet.getNeutered()),
			pet.getConditions() == null ? List.of() : List.copyOf(pet.getConditions())
		);
	}

	private UUID parseUuidOr404(String s, String kind) {
		try {
			return UUID.fromString(s);
		} catch (IllegalArgumentException exc) {
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", kind + " not found");
		}
	}
}
