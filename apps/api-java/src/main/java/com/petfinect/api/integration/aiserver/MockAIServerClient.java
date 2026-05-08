package com.petfinect.api.integration.aiserver;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.List;
import java.util.Map;

import com.petfinect.api.domain.DiagnosisAction;

/**
 * 결정론적 mock AI 서버 — sha256 기반 stable 응답.
 *
 * <p>Python {@code MockAIServerClient} 와 byte-for-byte 동일 출력 보장 (region 라벨 사전 +
 * 정규화 + threshold 모두 일치). dev/test/CI 에서 실 GPU 호출 없이 라우터·DB 계약 검증.
 *
 * <h3>알고리즘 (Python 측 동일)</h3>
 * <ol>
 *   <li>vision: {@code sha256(image_bytes || region_utf8)}</li>
 *   <li>{@code h[0..3]} 3바이트 → {@code [b/255.0]} 3개 → 내림차순 → 합 1 정규화</li>
 *   <li>top1 = scores[0] → {@link #actionFor(double)} 으로 action 결정</li>
 *   <li>audio: {@code sha256(audio_bytes)[0]/255.0} → 카테고리/action 결정</li>
 * </ol>
 *
 * <h3>학습 포인트</h3>
 * <ul>
 *   <li>Python 의 {@code zip(labels, scores, strict=False)} → Java 는 인덱스 기반 stream/loop.</li>
 *   <li>{@code Math.round} + {@code /10000.0} 로 4자리 반올림 — Python {@code round(x, 4)} 와 일치.</li>
 * </ul>
 */
public class MockAIServerClient implements AIServerClient {

	private static final Map<String, List<String>> REGION_LABELS = Map.of(
		"skin", List.of("skin_redness", "skin_normal", "skin_alopecia"),
		"eye", List.of("eye_discharge", "eye_normal", "eye_cataract"),
		"ear", List.of("ear_inflammation", "ear_normal", "ear_otitis"),
		"gum", List.of("gum_paleness", "gum_normal", "gum_periodontal")
	);
	private static final List<String> UNKNOWN_LABELS = List.of("unknown_a", "unknown_b", "unknown_c");

	@Override
	public VisionResult inferVision(byte[] imageBytes, String region) {
		byte[] regionBytes = region.getBytes(StandardCharsets.UTF_8);
		byte[] combined = new byte[imageBytes.length + regionBytes.length];
		System.arraycopy(imageBytes, 0, combined, 0, imageBytes.length);
		System.arraycopy(regionBytes, 0, combined, imageBytes.length, regionBytes.length);

		byte[] hash = sha256(combined);
		// h[0..3] 3바이트 → 0~1 점수 → 내림차순.
		double[] raw = new double[]{
			(hash[0] & 0xFF) / 255.0,
			(hash[1] & 0xFF) / 255.0,
			(hash[2] & 0xFF) / 255.0,
		};
		double[] sorted = sortDesc(raw);
		double total = sorted[0] + sorted[1] + sorted[2];
		if (total == 0.0) {
			total = 1.0;  // 모든 바이트 0 → 분모 0 회피 (Python 도 동일).
		}
		double[] normalized = new double[]{ sorted[0] / total, sorted[1] / total, sorted[2] / total };

		List<String> labels = REGION_LABELS.getOrDefault(region, UNKNOWN_LABELS);
		List<VisionTopResult> top = List.of(
			new VisionTopResult(labels.get(0), round4(normalized[0])),
			new VisionTopResult(labels.get(1), round4(normalized[1])),
			new VisionTopResult(labels.get(2), round4(normalized[2]))
		);
		double top1 = normalized[0];
		return new VisionResult(top, actionFor(top1), round4(top1));
	}

	@Override
	public AudioResult inferAudio(byte[] audioBytes) {
		byte[] hash = sha256(audioBytes);
		double score = (hash[0] & 0xFF) / 255.0;
		return new AudioResult(
			audioCategoryFor(score),
			round4(score),
			actionFor(score),
			round4(score)
		);
	}

	static DiagnosisAction actionFor(double score) {
		if (score >= 0.8) {
			return DiagnosisAction.immediate;
		}
		if (score >= 0.5) {
			return DiagnosisAction.schedule;
		}
		return DiagnosisAction.observe;
	}

	static String audioCategoryFor(double score) {
		if (score >= 0.8) {
			return "이상호흡";
		}
		if (score >= 0.6) {
			return "기침";
		}
		if (score >= 0.3) {
			return "꼬르륵";
		}
		return "정상";
	}

	private static byte[] sha256(byte[] input) {
		try {
			return MessageDigest.getInstance("SHA-256").digest(input);
		} catch (NoSuchAlgorithmException e) {
			throw new IllegalStateException("SHA-256 미지원", e);
		}
	}

	private static double[] sortDesc(double[] in) {
		double[] out = in.clone();
		// 3개 원소 → 직접 비교 (Arrays.sort 후 reverse 보다 명료).
		for (int i = 0; i < out.length; i++) {
			for (int j = i + 1; j < out.length; j++) {
				if (out[j] > out[i]) {
					double tmp = out[i];
					out[i] = out[j];
					out[j] = tmp;
				}
			}
		}
		return out;
	}

	private static double round4(double v) {
		return Math.round(v * 10000.0) / 10000.0;
	}
}
