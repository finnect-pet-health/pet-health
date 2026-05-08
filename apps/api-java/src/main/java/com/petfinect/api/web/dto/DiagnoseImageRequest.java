package com.petfinect.api.web.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * {@code POST /v1/diagnose/image} 요청 body.
 *
 * <p>Python {@code DiagnoseImageIn} 과 schema 동등 (camelCase 변환).
 *
 * <h3>region</h3>
 * <ul>
 *   <li>{@code skin / eye / ear / gum} 중 하나. 미입력/blank → 서비스에서 {@code skin} 기본값.</li>
 *   <li>알 수 없는 값도 통과 — Mock AI 가 {@code unknown_*} 라벨로 응답 (Python 동일).
 *       엄격 검증을 원하면 enum 또는 {@code @Pattern} 으로 강화.</li>
 * </ul>
 */
public record DiagnoseImageRequest(
	@NotBlank String petId,
	@NotBlank String imageS3Key,
	String region
) {}
