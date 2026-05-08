package com.petfinect.api.web.dto;

import java.time.OffsetDateTime;
import java.util.UUID;

public record MemberDetailResponse(
	UUID userId,
	String name,
	String role,
	OffsetDateTime joinedAt
) {}
