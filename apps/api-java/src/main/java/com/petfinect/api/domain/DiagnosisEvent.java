package com.petfinect.api.domain;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 진단 이벤트 — 이미지/오디오 결과 저장 (W3).
 *
 * <p>{@code top_results} 는 다양한 모달리티의 결과를 단일 JSONB 배열로 저장:
 * <ul>
 *   <li>image: {@code [{"label":"skin_redness","score":0.71}, ...]}</li>
 *   <li>audio: {@code [{"category":"기침","score":0.62}]}</li>
 * </ul>
 */
@Entity
@Table(
	name = "diagnosis_event",
	indexes = @Index(name = "ix_diagnosis_event_pet_created", columnList = "pet_id,created_at")
)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class DiagnosisEvent {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "pet_id", nullable = false)
	private Pet pet;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "modality", nullable = false, columnDefinition = "diagnosis_modality")
	private DiagnosisModality modality;

	@Column(name = "s3_ref", nullable = false)
	private String s3Ref;

	@JdbcTypeCode(SqlTypes.JSON)
	@Column(name = "top_results", nullable = false, columnDefinition = "jsonb")
	@Builder.Default
	private List<Map<String, Object>> topResults = new ArrayList<>();

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "action", nullable = false, columnDefinition = "diagnosis_action")
	private DiagnosisAction action;

	@Column(name = "confidence_top1", nullable = false)
	private Double confidenceTop1;

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;
}
