package com.petfinect.api.web;

import java.util.List;
import java.util.Map;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.petfinect.api.domain.DiagnosisEvent;
import com.petfinect.api.security.JwtAuthenticationFilter.AuthenticatedUser;
import com.petfinect.api.service.DiagnoseService;
import com.petfinect.api.web.dto.DiagnoseAudioRequest;
import com.petfinect.api.web.dto.DiagnoseImageRequest;
import com.petfinect.api.web.dto.DiagnosisResponse;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * Phase 8 — 진단 라우트.
 *
 * <h3>엔드포인트 (Python {@code apps/api/app/api/v1/diagnose.py} 와 1:1)</h3>
 * <ul>
 *   <li>{@code POST /v1/diagnose/image} — 이미지 진단</li>
 *   <li>{@code POST /v1/diagnose/audio} — 오디오 진단</li>
 *   <li>{@code GET  /v1/pets/{petId}/diagnoses?limit=20} — 펫별 진단 이력 (created_at DESC)</li>
 * </ul>
 *
 * <h3>{@code @Validated} 가 필요한 이유</h3>
 * <ul>
 *   <li>메서드 파라미터 단위 제약 ({@code @Min}/{@code @Max} on {@code int limit}) 을 활성화하려면
 *       클래스에 {@link Validated} 가 필요. {@code @Valid} 는 body 객체용.</li>
 *   <li>위반 시 {@code ConstraintViolationException} →
 *       {@link com.petfinect.api.web.exception.GlobalExceptionHandler} 가 400 으로 변환.</li>
 * </ul>
 */
@RestController
@Validated
@RequestMapping("")
public class DiagnoseController {

	private final DiagnoseService service;

	public DiagnoseController(DiagnoseService service) {
		this.service = service;
	}

	@PostMapping("/v1/diagnose/image")
	public DiagnosisResponse diagnoseImage(
		@Valid @RequestBody DiagnoseImageRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		DiagnosisEvent evt = service.diagnoseImage(
			principal.claims().sub(),
			req.petId(),
			req.imageS3Key(),
			req.region()
		);
		return serialize(evt);
	}

	@PostMapping("/v1/diagnose/audio")
	public DiagnosisResponse diagnoseAudio(
		@Valid @RequestBody DiagnoseAudioRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		DiagnosisEvent evt = service.diagnoseAudio(
			principal.claims().sub(),
			req.petId(),
			req.audioS3Key()
		);
		return serialize(evt);
	}

	@GetMapping("/v1/pets/{petId}/diagnoses")
	public List<DiagnosisResponse> listForPet(
		@PathVariable String petId,
		@RequestParam(defaultValue = "20") @Min(1) @Max(100) int limit,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		// petId path 변수가 PetController 의 매핑과 prefix 충돌하지 않음:
		// PetController 는 /v1/pets/{petId} 자체만 매핑 → /v1/pets/{petId}/diagnoses 와 분리.
		return service.listForPet(principal.claims().sub(), petId, limit).stream()
			.map(this::serialize)
			.toList();
	}

	private DiagnosisResponse serialize(DiagnosisEvent evt) {
		List<Map<String, Object>> top = evt.getTopResults() == null
			? List.of()
			: List.copyOf(evt.getTopResults());
		return new DiagnosisResponse(
			evt.getId(),
			evt.getPet().getId(),
			evt.getModality().name(),
			evt.getS3Ref(),
			top,
			evt.getAction().name(),
			evt.getConfidenceTop1(),
			evt.getCreatedAt()
		);
	}
}
