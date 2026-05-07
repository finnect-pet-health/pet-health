package com.petfinect.api.domain;

import java.io.Serializable;
import java.util.UUID;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * {@link FamilyMember} 의 composite PK 클래스.
 *
 * <h3>패턴</h3>
 * <ul>
 *   <li>{@link Serializable} 의무 — JPA 가 PK 인스턴스를 직렬화.</li>
 *   <li>{@code equals}/{@code hashCode}: 모든 컴포넌트 키 사용. Lombok
 *       {@code @EqualsAndHashCode} 자동.</li>
 *   <li>FamilyMember 측에서 {@code @IdClass(FamilyMemberId.class)} 로 연결.</li>
 * </ul>
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class FamilyMemberId implements Serializable {

	private UUID familyId;
	private UUID userId;
}
