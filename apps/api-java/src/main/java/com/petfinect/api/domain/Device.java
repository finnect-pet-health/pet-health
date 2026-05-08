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
 * Expo 푸시 디바이스 등록.
 *
 * <p>V8: expo_token 글로벌 UNIQUE → (user_id, expo_token) 복합 UNIQUE.
 * Expo 토큰은 단말 재설치/재발급 시 다른 user 에게 재할당될 수 있어
 * 글로벌 UNIQUE 면 INSERT 가 막힘.
 */
@Entity
@Table(
	name = "device",
	uniqueConstraints = @UniqueConstraint(
		name = "uq_device_user_expo_token",
		columnNames = {"user_id", "expo_token"}
	),
	indexes = @Index(name = "ix_device_user", columnList = "user_id")
)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Device {

	@Id
	@GeneratedValue(strategy = GenerationType.UUID)
	private UUID id;

	@ManyToOne(fetch = FetchType.LAZY)
	@JoinColumn(name = "user_id", nullable = false)
	private User user;

	@Column(name = "expo_token", nullable = false)
	private String expoToken;

	@Enumerated(EnumType.STRING)
	@JdbcTypeCode(SqlTypes.NAMED_ENUM)
	@Column(name = "platform", nullable = false, columnDefinition = "device_platform")
	private DevicePlatform platform;

	@Column(name = "last_seen_at", nullable = false)
	@Builder.Default
	private OffsetDateTime lastSeenAt = OffsetDateTime.now();

	@CreationTimestamp
	@Column(name = "created_at", nullable = false, updatable = false)
	private OffsetDateTime createdAt;
}
