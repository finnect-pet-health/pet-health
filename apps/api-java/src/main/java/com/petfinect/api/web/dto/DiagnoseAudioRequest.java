package com.petfinect.api.web.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * {@code POST /v1/diagnose/audio} 요청 body.
 *
 * <p>Python {@code DiagnoseAudioIn} 과 schema 동등 (camelCase 변환).
 */
public record DiagnoseAudioRequest(
	@NotBlank String petId,
	@NotBlank String audioS3Key
) {}
