package com.petfinect.api.web.dto;

import java.util.UUID;

public record FamilySummary(
	UUID id,
	String name,
	String role,
	int memberCount
) {}
