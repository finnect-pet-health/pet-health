package com.petfinect.api.security;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * JWT access token 의 클레임 표현.
 *
 * <h3>Java record 패턴</h3>
 * <ul>
 *   <li>{@code record} — Java 16+ 의 immutable value class.
 *       getter/equals/hashCode/toString 자동 생성. Python 의 frozen dataclass 와 같은 자리.</li>
 *   <li>모든 필드 final. 클레임은 토큰 발급 후 변경 불가능해야 하므로 record 가 적절.</li>
 * </ul>
 *
 * <h3>클레임 schema (Python {@code app.security.jwt.AccessClaims} 과 1:1)</h3>
 * <ul>
 *   <li>{@code sub} — 사용자 UUID 문자열</li>
 *   <li>{@code fids} — 사용자가 속한 family UUID 문자열 목록</li>
 *   <li>{@code roles} — {fid: role} 매핑. RBAC 검증 시 {@code roles.get(fid)} 으로 조회</li>
 *   <li>{@code exp} — 만료 unix timestamp (초)</li>
 * </ul>
 */
public record AccessClaims(
	UUID sub,
	List<UUID> fids,
	Map<UUID, String> roles,
	long exp
) {
	public boolean hasRoleIn(UUID familyId, String... allowed) {
		String role = roles.get(familyId);
		if (role == null) return false;
		for (String a : allowed) {
			if (a.equals(role)) return true;
		}
		return false;
	}
}
