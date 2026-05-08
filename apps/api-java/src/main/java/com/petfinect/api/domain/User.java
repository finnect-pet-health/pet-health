package com.petfinect.api.domain;

import java.time.OffsetDateTime;
import java.util.UUID;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

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
 * 사용자 — 카카오 OAuth 로 가입.
 *
 * <h3>주요 패턴</h3>
 * <ul>
 *   <li>{@code @Entity} + {@code @Table}: JPA 엔티티 마킹 + 테이블명/제약 매핑.
 *       {@code "user"} 는 PostgreSQL 예약어라 quote 필요 → {@code @Table(name = "\"user\"")}.</li>
 *   <li>{@code @Id} + {@code GenerationType.UUID}: PK 자동 생성. Hibernate 6 부터 UUID
 *       generation 표준 지원 (별도 generator 어노테이션 불필요).</li>
 *   <li>{@code @CreationTimestamp}: INSERT 시 timestamp 자동 셋. Hibernate 한정 어노테이션.</li>
 *   <li>Lombok {@code @Builder} + {@code @AllArgsConstructor}: 테스트/팩토리에서
 *       {@code User.builder().kakaoId("k").name("...").build()} 사용 가능.</li>
 *   <li>{@code @NoArgsConstructor(access = PROTECTED)}: JPA 가 reflection 으로 인스턴스
 *       만들 때만 사용. 실 코드에선 builder 강제 → 잘못된 빈 객체 방지.</li>
 * </ul>
 */
@Entity
@Table(
	name = "\"user\"",
	uniqueConstraints = @UniqueConstraint(name = "uq_user_kakao_id", columnNames = "kakao_id"),
	indexes = @Index(name = "ix_user_kakao_id", columnList = "kakao_id")
)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@Column(name = "kakao_id", nullable = false)
	private String kakaoId;

	@Column
	private String email;

	@Column(nullable = false)
	private String name;

	@Column(name = "profile_image")
	private String profileImage;

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;

	@Column(name = "last_login_at")
	private OffsetDateTime lastLoginAt;

	// V6: INSERT 시 DB DEFAULT now() (insertable=false), UPDATE 시 trigger.
	@UpdateTimestamp
	@Column(name = "updated_at", nullable = false, insertable = false)
	private OffsetDateTime updatedAt;
}
