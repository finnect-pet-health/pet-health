package com.petfinect.api.service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.UUID;

import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.petfinect.api.domain.DiagnosisAction;
import com.petfinect.api.domain.DiagnosisEvent;
import com.petfinect.api.domain.DiagnosisModality;
import com.petfinect.api.domain.Pet;
import com.petfinect.api.integration.aiserver.AIServerClient;
import com.petfinect.api.integration.aiserver.AudioResult;
import com.petfinect.api.integration.aiserver.VisionResult;
import com.petfinect.api.integration.aiserver.VisionTopResult;
import com.petfinect.api.integration.storage.StorageProvider;
import com.petfinect.api.repository.DiagnosisEventRepository;
import com.petfinect.api.web.exception.ApiException;

/**
 * Phase 8 — 진단 오케스트레이션.
 *
 * <h3>흐름 (Python {@code app.services.diagnose} 와 1:1)</h3>
 * <ol>
 *   <li>Pet RBAC 검증 — {@link PetService#getForUser} 가 다른 가족 펫이면 404.</li>
 *   <li>Storage 에서 객체 bytes fetch.</li>
 *   <li>{@link AIServerClient} 로 추론 (mock 또는 real).</li>
 *   <li>{@link DiagnosisEvent} 적재 후 반환.</li>
 * </ol>
 *
 * <h3>학습 포인트: 트랜잭션 경계</h3>
 * <ul>
 *   <li>외부 호출 (storage fetch + AI infer) 도 같은 {@code @Transactional} 안에 두면
 *       DB 커넥션이 외부 호출 동안 점유됨 — 일반적으론 분리하는 게 좋음.</li>
 *   <li>학습 자료에선 단일 트랜잭션 안에 둠: 적재 실패 시 롤백 단순. 운영에선
 *       조회/외부호출/저장을 메서드 단위로 분리하거나 {@code @Transactional} 을 persist 만 감싸도록 좁히는 게 권장.</li>
 * </ul>
 */
@Service
public class DiagnoseService {

	private static final String DEFAULT_REGION = "skin";

	private final PetService petService;
	private final StorageProvider storage;
	private final AIServerClient ai;
	private final DiagnosisEventRepository repository;

	public DiagnoseService(
		PetService petService,
		StorageProvider storage,
		AIServerClient ai,
		DiagnosisEventRepository repository
	) {
		this.petService = petService;
		this.storage = storage;
		this.ai = ai;
		this.repository = repository;
	}

	@Transactional
	public DiagnosisEvent diagnoseImage(UUID userId, String petIdStr, String s3Key, String region) {
		Pet pet = ensurePetAccess(userId, petIdStr);
		byte[] bytes = fetchOrThrow(s3Key);
		String effectiveRegion = (region == null || region.isBlank()) ? DEFAULT_REGION : region;
		VisionResult result = ai.inferVision(bytes, effectiveRegion);
		return persist(
			pet,
			DiagnosisModality.image,
			s3Key,
			toMaps(result.topResults()),
			result.action(),
			result.confidenceTop1()
		);
	}

	@Transactional
	public DiagnosisEvent diagnoseAudio(UUID userId, String petIdStr, String s3Key) {
		Pet pet = ensurePetAccess(userId, petIdStr);
		byte[] bytes = fetchOrThrow(s3Key);
		AudioResult result = ai.inferAudio(bytes);
		Map<String, Object> entry = new LinkedHashMap<>();
		entry.put("category", result.category());
		entry.put("score", result.score());
		return persist(
			pet,
			DiagnosisModality.audio,
			s3Key,
			List.of(entry),
			result.action(),
			result.confidenceTop1()
		);
	}

	@Transactional(readOnly = true)
	public List<DiagnosisEvent> listForPet(UUID userId, String petIdStr, int limit) {
		Pet pet = ensurePetAccess(userId, petIdStr);
		return repository.findByPetIdOrderByCreatedAtDesc(pet.getId(), PageRequest.of(0, limit));
	}

	private Pet ensurePetAccess(UUID userId, String petIdStr) {
		UUID petId;
		try {
			petId = UUID.fromString(petIdStr);
		} catch (IllegalArgumentException exc) {
			// 존재 누설 방지 — invalid UUID 도 펫 not found 와 동일 응답.
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "pet not found");
		}
		return petService.getForUser(petId, userId);
	}

	private byte[] fetchOrThrow(String key) {
		try {
			return storage.fetchBytes(key);
		} catch (NoSuchElementException exc) {
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "object not found: " + key);
		}
	}

	private DiagnosisEvent persist(
		Pet pet,
		DiagnosisModality modality,
		String s3Ref,
		List<Map<String, Object>> topResults,
		DiagnosisAction action,
		double confidenceTop1
	) {
		DiagnosisEvent evt = DiagnosisEvent.builder()
			.pet(pet)
			.modality(modality)
			.s3Ref(s3Ref)
			.topResults(topResults)
			.action(action)
			.confidenceTop1(confidenceTop1)
			.build();
		// saveAndFlush 로 @CreationTimestamp 가 INSERT 직후 즉시 보장되도록.
		// 같은 트랜잭션 안에서 응답 직렬화에 createdAt 을 사용하기 위함.
		return repository.saveAndFlush(evt);
	}

	private static List<Map<String, Object>> toMaps(List<VisionTopResult> top) {
		return top.stream().map(r -> {
			Map<String, Object> m = new LinkedHashMap<>();
			m.put("label", r.label());
			m.put("score", r.score());
			return m;
		}).toList();
	}
}
