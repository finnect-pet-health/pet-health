package com.petfinect.api.domain;

/**
 * {@code meal_food_kind} — 한국어 enum 값 그대로 매핑 ('사료'/'간식'/'일반식'/'처방식').
 *
 * Java enum 식별자는 한국어를 허용하지만 가독성을 위해 영어 식별자 + {@code @JsonProperty}
 * 또는 별도 매핑 함수를 권장. 본 학습 자료에서는 단순화 위해 한국어 식별자 사용.
 */
public enum MealFoodKind {
	사료,
	간식,
	일반식,
	처방식,
}
