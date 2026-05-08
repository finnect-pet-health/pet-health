package com.petfinect.api.web.dto;

import java.util.Map;

/**
 * {@code POST /v1/families} 응답 — Python {@code CreateFamilyOut} contract 동일.
 *
 * <p>{@code member} 는 {@code {"role": "owner"}} 형태. 향후 확장 여지를 위해 Map 사용.
 */
public record CreateFamilyResponse(FamilyDetail family, Map<String, String> member) {}
