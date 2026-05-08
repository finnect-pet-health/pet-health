package com.petfinect.api.web.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record FamilyCreateRequest(
	@NotBlank @Size(max = 100) String name
) {}
