package com.petfinect.api.domain;

/**
 * {@code meal_food_kind} — 영문 키 enum.
 *
 * <p>V10: 한글값 ('사료'/'간식'/'일반식'/'처방식') → 영문 키
 * ('kibble'/'treat'/'regular'/'prescription'). 라벨 i18n 은 클라이언트가
 * 매핑.
 */
public enum MealFoodKind {
	kibble,
	treat,
	regular,
	prescription,
}
