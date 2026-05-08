package com.petfinect.api.integration.storage;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class ModalityTest {

	@Test
	void image_allowsJpegPng_rejectsAudio() {
		assertThat(Modality.image.allowedContentTypes()).contains("image/jpeg", "image/png");
		assertThat(Modality.image.allowedContentTypes()).doesNotContain("audio/wav");
	}

	@Test
	void audio_allowsWavMp3M4a_rejectsImage() {
		assertThat(Modality.audio.allowedContentTypes()).contains("audio/wav", "audio/mpeg", "audio/m4a", "audio/mp4");
		assertThat(Modality.audio.allowedContentTypes()).doesNotContain("image/jpeg");
	}

	@Test
	void allUploadTypes_unionsBoth() {
		assertThat(Modality.allUploadTypes()).contains("image/jpeg", "audio/wav");
	}
}
