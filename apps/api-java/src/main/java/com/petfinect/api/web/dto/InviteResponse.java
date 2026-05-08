package com.petfinect.api.web.dto;

import java.time.OffsetDateTime;

public record InviteResponse(String inviteCode, OffsetDateTime expiresAt) {}
