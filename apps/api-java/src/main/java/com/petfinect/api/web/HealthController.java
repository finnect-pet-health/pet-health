package com.petfinect.api.web;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 단일 헬스체크 — Phase 0 scaffold 검증용. 추후 Spring Boot Actuator
 * /actuator/health 와 병행. PetFinect 모바일 앱은 /healthz 만 사용.
 */
@RestController
public class HealthController {

	@GetMapping("/healthz")
	public Map<String, String> healthz() {
		return Map.of("status", "ok");
	}
}
