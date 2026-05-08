package com.petfinect.api.integration.aiserver;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import com.petfinect.api.domain.DiagnosisAction;

/**
 * 비전 추론 결과 — top-K + 권장 행동 + top1 신뢰도.
 *
 * <p>AI 서버 응답 스키마 ({@code POST /infer/vision}) 와 1:1.
 *
 * <h3>JSON 매핑</h3>
 * <ul>
 *   <li>Python 측 필드는 snake_case ({@code top_results, confidence_top1}).</li>
 *   <li>Java record 의 component 명은 camelCase 가 관용 — {@link JsonProperty} 로 와이어 호환.</li>
 *   <li>대안: {@code application.yml} 에서 {@code spring.jackson.property-naming-strategy=SNAKE_CASE}
 *       전역 설정 가능. 본 프로젝트는 외부 계약 (Kakao, AI server) 에만 국한된 스키마이므로
 *       필드별 명시가 더 안전.</li>
 * </ul>
 */
public record VisionResult(
	@JsonProperty("top_results") List<VisionTopResult> topResults,
	DiagnosisAction action,
	@JsonProperty("confidence_top1") double confidenceTop1
) {
}
