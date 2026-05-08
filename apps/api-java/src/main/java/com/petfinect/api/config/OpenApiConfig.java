package com.petfinect.api.config;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;

import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;

import io.swagger.v3.core.jackson.ModelResolver;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;

/**
 * Phase 9 — springdoc-openapi 메타데이터 + Bearer 보안 스킴.
 *
 * <h3>왜 별도 클래스인가</h3>
 * <ul>
 *   <li>{@code application.yml} 의 {@code springdoc.*} 만으로는 보안 스킴 등록이 안 된다.</li>
 *   <li>Python {@code apps/api/app/main.py} 의 {@code FastAPI(title=..., version=...)} 와
 *       동일한 메타를 노출해 {@code packages/shared-types} 의 codegen 결과가
 *       기존 {@code docs/api/openapi-w3-v2.json} 과 1:1 호환되도록 한다.</li>
 * </ul>
 *
 * <h3>Bearer 스킴의 의미</h3>
 * <ul>
 *   <li>{@code SecurityRequirement("bearer-jwt")} 를 글로벌로 추가 → 모든 라우트에
 *       기본 Authorization 헤더 요구를 표시. {@code permitAll()} 라우트는 컨트롤러
 *       단위에서 {@code @SecurityRequirements({})} 로 끄거나, codegen 단계에선 그대로 둔다.</li>
 *   <li>{@code openapi-typescript} 는 보안 요구사항을 path option 에만 반영하므로
 *       타입 호환에는 영향 없음.</li>
 * </ul>
 */
@Configuration
public class OpenApiConfig {

	/**
	 * springdoc 의 swagger-core {@link ModelResolver} 에 Spring HTTP 직렬화와 같은
	 * SNAKE_CASE 전략을 가진 ObjectMapper 를 주입. 기본 동작은 swagger-core 내부의
	 * plain ObjectMapper (camelCase) 라 Java field 명이 그대로 schema 에 노출되어
	 * Python FastAPI 와 contract drift 가 발생한다.
	 *
	 * <p>Spring Boot 4 의 slim {@code spring-boot-starter-webmvc} 는 ObjectMapper 빈을
	 * 자동 등록하지 않으므로 이 빈은 별도 인스턴스로 만든다. HTTP 직렬화에 영향 없음
	 * (그쪽은 application.yml 의 {@code spring.jackson.property-naming-strategy} 가 담당).
	 *
	 * <p>참고: <a href="https://springdoc.org/#how-can-i-translate-the-openapi-output">
	 * springdoc FAQ — Jackson naming strategy 적용</a>.
	 */
	@Bean
	public ModelResolver modelResolver() {
		ObjectMapper mapper = new ObjectMapper();
		mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
		return new ModelResolver(mapper);
	}

	/**
	 * Python FastAPI 와 contract 정렬을 위한 두 가지 후처리:
	 *
	 * <h3>(1) required-by-default (Pydantic 시맨틱)</h3>
	 * Java record component 는 nullable/non-null 구분이 타입 레벨에 없어 springdoc 가
	 * 모든 응답 필드를 optional 로 출력 → mobile 의 typecheck 에서 {@code string | undefined}
	 * 가 강제 string 자리에 안 맞아 깨진다.
	 * <ul>
	 *   <li>이름이 {@code *Request} 로 끝나는 schema → Bean Validation ({@code @NotBlank} 등)
	 *       에 의존. {@code @Size}/{@code @Min} 만 있는 optional 필드는 그대로 둔다.</li>
	 *   <li>그 외 (응답 DTO) → 모든 properties 를 required 로 마킹.</li>
	 * </ul>
	 *
	 * <h3>(2) Map&lt;String, Object&gt; → additionalProperties: true</h3>
	 * Java {@code Map<String, Object>} 는 springdoc 에서
	 * {@code {type: object, additionalProperties: {type: object}}} 로 렌더링.
	 * Pydantic 의 {@code Dict[str, Any]} 는 {@code additionalProperties: true} 라
	 * openapi-typescript 가 전자는 {@code Record<string, never>}, 후자는
	 * {@code {[key: string]: unknown}} 으로 변환 → 호환성 깨짐.
	 * 모든 schema 트리를 재귀하며 빈 {@code {type: object}} additionalProperties 를
	 * {@code true} 로 평탄화.
	 */
	@Bean
	public OpenApiCustomizer responseFieldsRequiredCustomizer() {
		return openApi -> {
			if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
				return;
			}
			openApi.getComponents().getSchemas().forEach((name, schema) -> {
				if (!name.endsWith("Request") && schema.getProperties() != null) {
					schema.setRequired(new ArrayList<>(schema.getProperties().keySet()));
				}
				flattenOpenObjectAdditionalProperties(schema, new HashSet<>());
			});
		};
	}

	/**
	 * 재귀적으로 schema 트리를 돌며 {@code additionalProperties} 가
	 * 다른 제약 없는 {@code Schema{type=object}} 인 노드를 발견하면 {@code Boolean.TRUE} 로 교체.
	 * IdentityHashMap 기반 visited 셋으로 schema graph 의 cycle 도 안전 처리.
	 */
	private static void flattenOpenObjectAdditionalProperties(Schema<?> schema, Set<Schema<?>> visited) {
		if (schema == null || !visited.add(schema)) return;
		Object ap = schema.getAdditionalProperties();
		if (ap instanceof Schema<?> apSchema && isOpenObjectSchema(apSchema)) {
			schema.setAdditionalProperties(Boolean.TRUE);
		} else if (ap instanceof Schema<?> apSchema) {
			flattenOpenObjectAdditionalProperties(apSchema, visited);
		}
		if (schema.getItems() != null) {
			flattenOpenObjectAdditionalProperties(schema.getItems(), visited);
		}
		if (schema.getProperties() != null) {
			schema.getProperties().values().forEach(v -> flattenOpenObjectAdditionalProperties(v, visited));
		}
	}

	private static boolean isOpenObjectSchema(Schema<?> s) {
		return "object".equals(s.getType())
			&& s.getProperties() == null
			&& s.getAdditionalProperties() == null
			&& s.get$ref() == null
			&& s.getFormat() == null
			&& s.getEnum() == null;
	}

	@Bean
	public OpenAPI petfinectOpenAPI() {
		return new OpenAPI()
			.info(new Info()
				.title("PetFinect API")
				.version("0.1.0")
				.description("PetFinect cloud API — Spring Boot 4 (Java 21) port. "
					+ "Contract identical to FastAPI baseline (apps/api).")
				.license(new License().name("Internal").url("https://petfinect.example/internal")))
			.addSecurityItem(new SecurityRequirement().addList("bearer-jwt"))
			.components(new Components()
				.addSecuritySchemes("bearer-jwt", new SecurityScheme()
					.type(SecurityScheme.Type.HTTP)
					.scheme("bearer")
					.bearerFormat("JWT")
					.description("JWT access token issued by /v1/auth/kakao or /v1/auth/refresh")));
	}
}
