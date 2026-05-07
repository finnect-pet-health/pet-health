package com.petfinect.api.domain;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

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
 * 펫 — Family 의 1:N 자식.
 *
 * <h3>JSONB 매핑</h3>
 * <ul>
 *   <li>{@code @JdbcTypeCode(SqlTypes.JSON)}: Hibernate 6 가 JSONB 컬럼에 List/Map 을
 *       자동 직렬화 (Jackson 사용). DB 측 {@code conditions JSONB DEFAULT '[]'} 과 1:1.</li>
 *   <li>List 초기값을 {@code new ArrayList<>()} 로 두면 builder 미사용 시에도 NPE 방지.</li>
 * </ul>
 */
@Entity
@Table(name = "pet")
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Pet {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "family_id", nullable = false)
	private Family family;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "species", nullable = false, columnDefinition = "pet_species")
	@Builder.Default
	private PetSpecies species = PetSpecies.dog;

	@Column
	private String breed;

	@Column
	private LocalDate dob;

	@Column
	private Double weight;

	@Column(nullable = false)
	@Builder.Default
	private Boolean neutered = false;

	@JdbcTypeCode(SqlTypes.JSON)
	@Column(nullable = false, columnDefinition = "jsonb")
	@Builder.Default
	private List<String> conditions = new ArrayList<>();
}
