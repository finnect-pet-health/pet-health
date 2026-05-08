package com.petfinect.api.domain;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
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

/** 식사 기록 (W2). pet 별 시계열. */
@Entity
@Table(name = "meal", indexes = @Index(name = "ix_meal_pet_ts", columnList = "pet_id,ts"))
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Meal {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "pet_id", nullable = false)
	private Pet pet;

	@Column(nullable = false)
	private OffsetDateTime ts;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "source", nullable = false, columnDefinition = "meal_source")
	private MealSource source;

	@Column(name = "food_id")
	private String foodId;

	@Column(name = "food_name", nullable = false)
	private String foodName;

	// V10: DOUBLE PRECISION → NUMERIC(10, 2) — 영양정보 정밀도 (BigDecimal).
	@Column(name = "qty_g", nullable = false)
	private BigDecimal qtyG;

	private BigDecimal kcal;

	@Column(name = "protein_g")
	private BigDecimal proteinG;

	@Column(name = "carbs_g")
	private BigDecimal carbsG;

	@Column(name = "fat_g")
	private BigDecimal fatG;

	private String note;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "food_kind", columnDefinition = "meal_food_kind")
	private MealFoodKind foodKind;

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;
}
