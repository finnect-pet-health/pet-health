package com.petfinect.api.domain;

/**
 * {@code diagnosis_action} — 권장 행동.
 * <ul>
 *   <li>{@code immediate}: 즉시 진료 (severe). 모바일 칩 빨강.</li>
 *   <li>{@code schedule}: 진료 예약 (moderate). 모바일 칩 노랑.</li>
 *   <li>{@code observe}: 관찰 (mild). 모바일 칩 파랑.</li>
 * </ul>
 */
public enum DiagnosisAction {
	immediate,
	schedule,
	observe,
}
