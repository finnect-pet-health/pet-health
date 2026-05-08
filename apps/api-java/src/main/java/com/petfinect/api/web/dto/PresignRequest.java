package com.petfinect.api.web.dto;

import com.petfinect.api.integration.storage.Modality;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record PresignRequest(
	@NotNull Modality modality,
	@NotBlank String contentType
) {}
