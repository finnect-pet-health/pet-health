package com.petfinect.api.web.dto;

import jakarta.validation.constraints.NotBlank;

public record JoinRequest(@NotBlank String inviteCode) {}
