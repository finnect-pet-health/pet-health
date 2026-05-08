package com.petfinect.api.web.dto;

import java.util.List;
import java.util.UUID;

public record MeResponse(
	UUID id,
	String name,
	String profileImage,
	List<FamilySummary> families
) {}
