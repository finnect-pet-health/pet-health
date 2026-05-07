package com.petfinect.api.domain;

/**
 * 가족 멤버 역할 — PostgreSQL native enum {@code member_role} 과 1:1.
 * RBAC 의 owner 는 member 의 모든 권한을 자동 포함 (서비스 계층에서 정책 결정).
 */
public enum MemberRole {
	owner,
	member,
}
