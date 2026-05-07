package com.petfinect.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import com.petfinect.api.web.HealthController;

/**
 * Phase 0 smoke — HealthController slice 만 부팅. DB/JPA/Flyway 미참여.
 * 통합 컨텍스트 부팅 + Flyway 통합 테스트는 Phase 1 (Testcontainers 도입) 후.
 */
@WebMvcTest(HealthController.class)
class PetfinectApiApplicationTests {

	@Autowired
	private MockMvc mockMvc;

	@Test
	@WithMockUser
	void healthzReturnsOk() throws Exception {
		mockMvc.perform(get("/healthz"))
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.status").value("ok"));
	}
}
