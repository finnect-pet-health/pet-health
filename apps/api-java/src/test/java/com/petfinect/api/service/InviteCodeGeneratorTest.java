package com.petfinect.api.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

import org.junit.jupiter.api.Test;

class InviteCodeGeneratorTest {

	private static final Pattern BASE32 = Pattern.compile("^[A-Z2-7]{8}$");

	@Test
	void generate_8charBase32() {
		InviteCodeGenerator gen = new InviteCodeGenerator();
		for (int i = 0; i < 50; i++) {
			String code = gen.generate();
			assertThat(code).hasSize(8);
			assertThat(BASE32.matcher(code).matches())
				.as("code %s is base32", code)
				.isTrue();
		}
	}

	@Test
	void generate_highEntropy() {
		InviteCodeGenerator gen = new InviteCodeGenerator();
		Set<String> seen = new HashSet<>();
		for (int i = 0; i < 100; i++) {
			seen.add(gen.generate());
		}
		// 100회 생성 시 중복은 사실상 불가능 (40 bits ~ 1조 가지 중에서 100개)
		assertThat(seen).hasSize(100);
	}
}
