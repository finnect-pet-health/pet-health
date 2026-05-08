package com.petfinect.api.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
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
 * 가족 — 한 명 이상의 사용자가 펫을 공유 관리하는 단위.
 *
 * <h3>관계 패턴</h3>
 * <ul>
 *   <li>{@code @ManyToOne(fetch = LAZY)}: owner 는 단일 User 를 참조. LAZY 로 N+1 회피.</li>
 *   <li>{@code @JoinColumn}: FK 컬럼 명시. {@code referencedColumnName} 생략 시 PK 자동.</li>
 * </ul>
 */
@Entity
@Table(name = "family")
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Family {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@Column(nullable = false)
	private String name;

	// onDelete=RESTRICT 정책: family 가 user 를 참조 — owner 삭제는 family 보호 위해 막힘.
	// JPA 측은 단순 ManyToOne; 실 정책은 V1__init.sql 의 ON DELETE RESTRICT.
	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "owner_id", nullable = false)
	private User owner;

	// V9: invite_code/invite_expires_at 은 family_invite 테이블로 이전.
	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;

	// V6: INSERT 시 DB DEFAULT now() (insertable=false), UPDATE 시 trigger.
	@UpdateTimestamp
	@Column(name = "updated_at", nullable = false, insertable = false)
	private OffsetDateTime updatedAt;
}
