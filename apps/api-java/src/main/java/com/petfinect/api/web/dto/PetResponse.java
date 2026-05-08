package com.petfinect.api.web.dto;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

public record PetResponse(
	UUID id,
	UUID familyId,
	String species,
	String breed,
	LocalDate dob,
	Double weight,
	boolean neutered,
	List<String> conditions
) {}
