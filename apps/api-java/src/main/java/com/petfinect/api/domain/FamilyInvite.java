package com.petfinect.api.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

import org.hibernate.annotations.CreationTimestamp;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * V9: family.invite_code/invite_expires_at 의 1:N 분리.
 *
 * <p>한 가족이 여러 invite 를 동시 발급/만료 가능. used_at/used_by 는 향후
 * 단일 사용 강제 시 사용할 감사 컬럼 (현재는 nullable, 미사용).
 */
@Entity
@Table(
	name = "family_invite",
	uniqueConstraints = @UniqueConstraint(name = "uq_family_invite_code", columnNames = "code"),
	indexes = @Index(name = "ix_family_invite_family_created", columnList = "family_id,created_at")
)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class FamilyInvite {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "family_id", nullable = false)
	private Family family;

	@Column(name = "code", nullable = false, length = 16)
	private String code;

	@Column(name = "expires_at", nullable = false)
	private OffsetDateTime expiresAt;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "created_by")
	private User createdBy;

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;

	@Column(name = "used_at")
	private OffsetDateTime usedAt;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "used_by")
	private User usedBy;
}
