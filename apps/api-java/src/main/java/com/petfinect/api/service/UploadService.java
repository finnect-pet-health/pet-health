package com.petfinect.api.service;

import java.util.Map;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import com.petfinect.api.integration.storage.Modality;
import com.petfinect.api.integration.storage.StorageProvider;
import com.petfinect.api.integration.storage.UnsupportedContentTypeException;
import com.petfinect.api.web.dto.PresignResponse;
import com.petfinect.api.web.dto.RawUploadResponse;
import com.petfinect.api.web.exception.ApiException;

/**
 * 업로드 도메인 서비스 — presign + raw upload.
 *
 * <h3>key 규칙 (Python 와 동일)</h3>
 * <p>{@code uploads/{modality}/{userId}/{uuid}.{ext}}
 *
 * <h3>content-type → 확장자 매핑</h3>
 * <p>presign 단계에서 키에 확장자를 박아 두면 backend/AI server 측이 modality 외에도
 * 직관적으로 분기 가능.
 */
@Service
public class UploadService {

	public static final int PRESIGN_TTL_SECONDS = 600;

	private static final Map<String, String> EXT_BY_TYPE = Map.of(
		"image/jpeg", "jpg",
		"image/png", "png",
		"audio/wav", "wav",
		"audio/mpeg", "mp3",
		"audio/m4a", "m4a",
		"audio/mp4", "m4a"
	);

	private final StorageProvider storage;
	private final String activeProfile;

	public UploadService(
		StorageProvider storage,
		@Value("${spring.profiles.active:default}") String activeProfile
	) {
		this.storage = storage;
		this.activeProfile = activeProfile;
	}

	public PresignResponse issuePresign(Modality modality, String contentType, UUID userId) {
		validateContentType(modality, contentType);
		String key = buildKey(modality, userId, contentType);
		String url = storage.presignPut(key, contentType, PRESIGN_TTL_SECONDS);
		return new PresignResponse(key, url, PRESIGN_TTL_SECONDS);
	}

	public RawUploadResponse rawUpload(String key, String contentType, byte[] body) {
		if ("production".equals(activeProfile)) {
			throw new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "raw upload disabled in production");
		}
		if (!Modality.allUploadTypes().contains(contentType)) {
			throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_CONTENT_TYPE", "'" + contentType + "' not allowed");
		}
		if (body == null || body.length == 0) {
			throw new ApiException(HttpStatus.BAD_REQUEST, "EMPTY_BODY", "empty upload body");
		}
		storage.putBytes(key, body, contentType);
		return new RawUploadResponse(key, body.length);
	}

	private void validateContentType(Modality modality, String contentType) {
		if (!modality.allowedContentTypes().contains(contentType)) {
			throw new UnsupportedContentTypeException(
				"content_type '" + contentType + "' not allowed for modality '" + modality + "'"
			);
		}
	}

	private String buildKey(Modality modality, UUID userId, String contentType) {
		String ext = EXT_BY_TYPE.get(contentType);
		return "uploads/" + modality + "/" + userId + "/" + UUID.randomUUID() + "." + ext;
	}
}
