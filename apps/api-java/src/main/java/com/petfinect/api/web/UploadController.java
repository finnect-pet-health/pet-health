package com.petfinect.api.web;

import java.io.IOException;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.servlet.http.HttpServletRequest;

import com.petfinect.api.integration.storage.UnsupportedContentTypeException;
import com.petfinect.api.security.JwtAuthenticationFilter.AuthenticatedUser;
import com.petfinect.api.service.UploadService;
import com.petfinect.api.web.dto.PresignRequest;
import com.petfinect.api.web.dto.PresignResponse;
import com.petfinect.api.web.dto.RawUploadResponse;
import com.petfinect.api.web.exception.ApiException;

import jakarta.validation.Valid;

/**
 * 업로드 라우트 — Python {@code apps/api/app/api/v1/uploads.py} 와 contract 동일.
 *
 * <h3>두 라우트의 의도</h3>
 * <ul>
 *   <li>{@code POST /v1/uploads/presign}: 운영 흐름 — 모바일이 직접 S3 PUT.</li>
 *   <li>{@code POST /v1/uploads/raw?key=...}: dev/mock — {@code mock-s3://} URL 인식한
 *       모바일 helper 가 backend 로 forward. production 에선 404.</li>
 * </ul>
 *
 * <h3>raw upload 의 body 처리</h3>
 * <ul>
 *   <li>{@code @RequestBody byte[]} — Spring 이 raw bytes 로 역직렬화. Content-Type 무관.</li>
 *   <li>큰 파일 들어오면 메모리 사용 ↑ → 운영 S3 직접 PUT 가 정답. dev 한정 사용.</li>
 * </ul>
 */
@RestController
@RequestMapping("/v1/uploads")
public class UploadController {

	private final UploadService uploadService;

	public UploadController(UploadService uploadService) {
		this.uploadService = uploadService;
	}

	@PostMapping("/presign")
	public PresignResponse presign(
		@Valid @RequestBody PresignRequest req,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		try {
			return uploadService.issuePresign(req.modality(), req.contentType(), principal.claims().sub());
		} catch (UnsupportedContentTypeException exc) {
			throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_CONTENT_TYPE", exc.getMessage());
		}
	}

	@PostMapping("/raw")
	public RawUploadResponse raw(
		@RequestParam String key,
		@RequestHeader("Content-Type") String contentType,
		HttpServletRequest request,
		@AuthenticationPrincipal AuthenticatedUser principal
	) {
		// {@code @RequestBody byte[]} 는 빈 body 시 binding 실패 → 401 우회 발생.
		// HttpServletRequest 의 InputStream 을 직접 읽어 빈 body 도 controller 에 도달시킴.
		byte[] body;
		try {
			body = request.getInputStream().readAllBytes();
		} catch (IOException exc) {
			throw new ApiException(HttpStatus.BAD_REQUEST, "READ_FAILED", "failed to read request body");
		}
		return uploadService.rawUpload(key, contentType, body);
	}
}
