package com.petfinect.api.integration.aiserver;

import com.fasterxml.jackson.annotation.JsonProperty;

import com.petfinect.api.domain.DiagnosisAction;

/**
 * 오디오 추론 결과 — 카테고리 + score + action.
 *
 * <p>AI 서버 응답 ({@code POST /infer/audio}) 와 1:1.
 * 카테고리는 한국어 라벨 ({@code 정상/기침/이상호흡/꼬르륵/기타}) — Python {@code AudioCategory} 와 일치.
 */
public record AudioResult(
	String category,
	double score,
	DiagnosisAction action,
	@JsonProperty("confidence_top1") double confidenceTop1
) {
}
