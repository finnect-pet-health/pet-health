package com.petfinect.api.domain;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

import org.hibernate.annotations.UpdateTimestamp;
import org.locationtech.jts.geom.Point;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
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

/**
 * 동물병원 — data.go.kr ETL upsert 대상. 위치는 PostGIS POINT(SRID 4326).
 *
 * <h3>PostGIS 매핑 (Hibernate Spatial)</h3>
 * <ul>
 *   <li>JTS {@link Point} 타입을 직접 사용. {@code columnDefinition} 으로 SRID 4326 명시.</li>
 *   <li>insert 시 application 측에서 {@code GeometryFactory.createPoint(new Coordinate(lng, lat))}
 *       후 SRID 셋팅.</li>
 *   <li>{@code GiST} index 는 V3 migration 에서 직접 생성 — JPA 표현 불가.</li>
 * </ul>
 */
@Entity
@Table(
	name = "hospital",
	uniqueConstraints = @UniqueConstraint(name = "uq_hospital_mgmt_no", columnNames = "mgmt_no"),
	indexes = @Index(name = "ix_hospital_status", columnList = "status")
)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Hospital {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@Column(name = "mgmt_no", nullable = false)
	private String mgmtNo;

	@Column(nullable = false)
	private String name;

	@Column(name = "road_addr", nullable = false)
	@Builder.Default
	private String roadAddr = "";

	@Column(name = "lot_addr", nullable = false)
	@Builder.Default
	private String lotAddr = "";

	@Column(nullable = false)
	@Builder.Default
	private String zip = "";

	@Column(nullable = false)
	@Builder.Default
	private String tel = "";

	@Column(nullable = false)
	@Builder.Default
	private String status = "";

	// V7: VARCHAR(YYYYMMDD) → DATE. ETL 가 파싱 책임.
	@Column(name = "licensed_at")
	private LocalDate licensedAt;

	@Column(name = "authority_code", nullable = false)
	@Builder.Default
	private String authorityCode = "";

	@Column(columnDefinition = "geometry(Point, 4326)")
	private Point location;

	// INSERT 시 DB DEFAULT now() (V3 migration), UPDATE 시 @UpdateTimestamp 자동.
	@UpdateTimestamp
	@Column(name = "updated_at", nullable = false, insertable = false)
	private OffsetDateTime updatedAt;
}
