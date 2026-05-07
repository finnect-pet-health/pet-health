package com.petfinect.api.domain;

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
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.MapsId;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 가족 ↔ 사용자 멤버십 + RBAC 역할.
 *
 * <h3>Composite PK 패턴</h3>
 * <ul>
 *   <li>{@code @IdClass(FamilyMemberId.class)}: PK 가 두 컬럼으로 구성됨.</li>
 *   <li>{@code @Id} + {@code @ManyToOne} + {@code @MapsId}: ID 필드 자체가 FK 인 패턴 —
 *       별도 컬럼 추가 없이 family/user 참조와 PK 컴포넌트가 동일.</li>
 * </ul>
 *
 * <h3>PostgreSQL native enum 매핑</h3>
 * <ul>
 *   <li>{@code @JdbcTypeCode(SqlTypes.NAMED_ENUM)}: Hibernate 6.5+ 가 PostgreSQL 의
 *       {@code member_role} 타입과 자동 캐스팅. Java enum 식별자가 enum 라벨과 동일해야 함.</li>
 * </ul>
 */
@Entity
@Table(
	name = "family_member",
	indexes = @Index(name = "ix_family_member_user_id", columnList = "user_id")
)
@IdClass(FamilyMemberId.class)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class FamilyMember {

	@Id
	@Column(name = "family_id", nullable = false)
	private UUID familyId;

	@Id
	@Column(name = "user_id", nullable = false)
	private UUID userId;

	@ManyToOne(fetch = FetchType.LAZY)
	@MapsId("familyId")
	@JoinColumn(name = "family_id", nullable = false, insertable = false, updatable = false)
	private Family family;

	@ManyToOne(fetch = FetchType.LAZY)
	@MapsId("userId")
	@JoinColumn(name = "user_id", nullable = false, insertable = false, updatable = false)
	private User user;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "role", nullable = false, columnDefinition = "member_role")
	private MemberRole role;

	@CreationTimestamp
	@Column(name = "joined_at", nullable = false, updatable = false)
	private OffsetDateTime joinedAt;
}
