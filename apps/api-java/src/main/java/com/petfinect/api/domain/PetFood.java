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
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** 사료 카탈로그 — FatSecret + 자체 시드 200건 + 사용자 추가. */
@Entity
@Table(
	name = "pet_food",
	uniqueConstraints = @UniqueConstraint(name = "uq_pet_food_brand_name", columnNames = {"brand", "name"}),
	indexes = @Index(name = "ix_pet_food_brand", columnList = "brand")
)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PetFood {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@Column(nullable = false)
	private String brand;

	@Column(nullable = false)
	private String name;

	// V10: DOUBLE PRECISION → NUMERIC(10, 2). 컬럼명도 단위(per 100g) 명시.
	@Column(name = "kcal_per_100g", nullable = false)
	private BigDecimal kcalPer100g;

	@Column(name = "protein_per_100g")
	private BigDecimal proteinPer100g;

	@Column(name = "carbs_per_100g")
	private BigDecimal carbsPer100g;

	@Column(name = "fat_per_100g")
	private BigDecimal fatPer100g;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "source", nullable = false, columnDefinition = "pet_food_source")
	@Builder.Default
	private PetFoodSource source = PetFoodSource.seed;

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;
}
