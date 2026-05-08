package com.petfinect.api.integration.storage;

import java.util.Set;

/**
 * 업로드 modality.
 *
 * <p>enum constant 이름이 곧 JSON 직렬화 값 — lowercase 유지 (Python {@code Literal["image", "audio"]} 와 1:1).
 * 프로젝트 기존 enum 들 ({@code PetSpecies.dog}) 과 동일 컨벤션.
 */
@SuppressWarnings("java:S115")  // lowercase enum names: JSON contract 와 정렬
public enum Modality {
	image, audio;

	public static final Set<String> ALLOWED_IMAGE_TYPES = Set.of("image/jpeg", "image/png");
	public static final Set<String> ALLOWED_AUDIO_TYPES = Set.of(
		"audio/wav", "audio/mpeg", "audio/m4a", "audio/mp4"
	);

	public Set<String> allowedContentTypes() {
		return this == image ? ALLOWED_IMAGE_TYPES : ALLOWED_AUDIO_TYPES;
	}

	public static Set<String> allUploadTypes() {
		return Set.of(
			"image/jpeg", "image/png",
			"audio/wav", "audio/mpeg", "audio/m4a", "audio/mp4"
		);
	}
}
