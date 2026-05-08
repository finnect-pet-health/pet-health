package com.petfinect.api.web.dto;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

public record PetResponse(
	UUID id,
	UUID familyId,
	String name,
	String species,
	String breed,
	LocalDate dob,
	Double weight,
	boolean neutered,
	List<String> conditions,
	OffsetDateTime createdAt
) {}
