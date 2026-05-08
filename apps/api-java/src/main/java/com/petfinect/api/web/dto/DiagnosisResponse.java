package com.petfinect.api.web.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 진단 결과 응답 — Python {@code DiagnosisOut} 과 schema 동등 (camelCase 변환).
 *
 * <h3>{@code topResults}</h3>
 * <ul>
 *   <li>image: {@code [{label, score}, ...]}</li>
 *   <li>audio: {@code [{category, score}]}</li>
 * </ul>
 * 모달리티별 형태가 달라 {@code List<Map<String, Object>>} 로 일반화.
 * 모바일 클라이언트는 modality 로 분기해 키를 읽음.
 */
public record DiagnosisResponse(
	UUID id,
	UUID petId,
	String modality,
	String s3Ref,
	List<Map<String, Object>> topResults,
	String action,
	double confidenceTop1,
	OffsetDateTime createdAt
) {}
