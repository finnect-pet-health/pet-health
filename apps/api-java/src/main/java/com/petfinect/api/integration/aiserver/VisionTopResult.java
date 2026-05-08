package com.petfinect.api.integration.aiserver;

/**
 * 비전 추론 top-K 후보 1개.
 *
 * <p>Python {@code apps/api/app/integrations/ai_server/__init__.py} 의 동일 이름 BaseModel 과 1:1.
 *
 * <h3>학습 포인트: Java {@code record}</h3>
 * <ul>
 *   <li>Java 14+ 의 {@code record} 는 immutable 데이터 보유체 — Python {@code BaseModel} / Kotlin
 *       {@code data class} 와 같은 자리.</li>
 *   <li>자동 생성: canonical constructor, accessor (필드명 그대로), {@code equals/hashCode/toString}.</li>
 *   <li>Jackson 이 record 를 native 지원 — 별도 어노테이션 없이 JSON 역직렬화 가능.</li>
 * </ul>
 */
public record VisionTopResult(String label, double score) {
}
