package com.petfinect.api.integration.aiserver;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

import com.petfinect.api.domain.DiagnosisAction;

/**
 * 결정론적 mock 검증 — 동일 입력 → 동일 출력 + Python 알고리즘과 1:1.
 *
 * <h3>왜 이런 식으로 검증하는가</h3>
 * <ul>
 *   <li>실 모델 호출 없이 라우터 (Phase 8) 가 enum/JSON 매핑을 안전하게 수행하는지 확인.</li>
 *   <li>알고리즘 계약 (sha256 + 정규화 + threshold) 이 Python 측과 byte-for-byte 동일해야 모바일
 *       앱이 두 백엔드를 swap 해도 결과가 일치.</li>
 * </ul>
 */
class MockAIServerClientTest {

	private final MockAIServerClient client = new MockAIServerClient();

	@Test
	void inferVision_skin_isDeterministic() {
		byte[] payload = "sample-image".getBytes(StandardCharsets.UTF_8);
		VisionResult a = client.inferVision(payload, "skin");
		VisionResult b = client.inferVision(payload, "skin");
		assertThat(a).isEqualTo(b);
	}

	@Test
	void inferVision_skin_returnsSkinLabels() {
		VisionResult r = client.inferVision("x".getBytes(), "skin");
		assertThat(r.topResults()).hasSize(3);
		assertThat(r.topResults().stream().map(VisionTopResult::label).toList())
			.containsExactly("skin_redness", "skin_normal", "skin_alopecia");
	}

	@Test
	void inferVision_unknownRegion_fallsBackToUnknownLabels() {
		VisionResult r = client.inferVision("x".getBytes(), "wrist");
		assertThat(r.topResults().stream().map(VisionTopResult::label).toList())
			.containsExactly("unknown_a", "unknown_b", "unknown_c");
	}

	@Test
	void inferVision_scoresNormalizedToOne() {
		VisionResult r = client.inferVision("payload".getBytes(), "eye");
		double sum = r.topResults().stream().mapToDouble(VisionTopResult::score).sum();
		// round4 누적 오차 허용.
		assertThat(sum).isCloseTo(1.0, org.assertj.core.data.Offset.offset(0.001));
	}

	@Test
	void inferVision_top1MatchesFirstResult() {
		VisionResult r = client.inferVision("payload".getBytes(), "ear");
		assertThat(r.confidenceTop1()).isEqualTo(r.topResults().get(0).score());
	}

	@Test
	void inferVision_topDescending() {
		VisionResult r = client.inferVision("payload-zzz".getBytes(), "gum");
		double s0 = r.topResults().get(0).score();
		double s1 = r.topResults().get(1).score();
		double s2 = r.topResults().get(2).score();
		assertThat(s0).isGreaterThanOrEqualTo(s1);
		assertThat(s1).isGreaterThanOrEqualTo(s2);
	}

	@Test
	void inferAudio_isDeterministic() {
		byte[] payload = "audio-sample".getBytes(StandardCharsets.UTF_8);
		AudioResult a = client.inferAudio(payload);
		AudioResult b = client.inferAudio(payload);
		assertThat(a).isEqualTo(b);
	}

	@Test
	void inferAudio_categoryIsKoreanLabel() {
		AudioResult r = client.inferAudio("audio".getBytes());
		assertThat(r.category()).isIn("정상", "기침", "이상호흡", "꼬르륵");
	}

	@Test
	void actionFor_thresholds() {
		assertThat(MockAIServerClient.actionFor(0.85)).isEqualTo(DiagnosisAction.immediate);
		assertThat(MockAIServerClient.actionFor(0.80)).isEqualTo(DiagnosisAction.immediate);
		assertThat(MockAIServerClient.actionFor(0.79)).isEqualTo(DiagnosisAction.schedule);
		assertThat(MockAIServerClient.actionFor(0.50)).isEqualTo(DiagnosisAction.schedule);
		assertThat(MockAIServerClient.actionFor(0.49)).isEqualTo(DiagnosisAction.observe);
		assertThat(MockAIServerClient.actionFor(0.0)).isEqualTo(DiagnosisAction.observe);
	}

	@Test
	void audioCategoryFor_thresholds() {
		assertThat(MockAIServerClient.audioCategoryFor(0.85)).isEqualTo("이상호흡");
		assertThat(MockAIServerClient.audioCategoryFor(0.65)).isEqualTo("기침");
		assertThat(MockAIServerClient.audioCategoryFor(0.40)).isEqualTo("꼬르륵");
		assertThat(MockAIServerClient.audioCategoryFor(0.20)).isEqualTo("정상");
	}
}
