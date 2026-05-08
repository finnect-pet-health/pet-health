package com.petfinect.api.web.dto;

public record PresignResponse(String key, String url, int ttlS) {}
