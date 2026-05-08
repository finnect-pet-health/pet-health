package com.petfinect.api.integration.storage;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.NoSuchElementException;

import org.junit.jupiter.api.Test;

class InMemoryStorageTest {

	@Test
	void putBytes_thenFetch_roundTrip() {
		InMemoryStorage storage = new InMemoryStorage("bucket-1");
		byte[] data = "hello world".getBytes();

		storage.putBytes("k1", data, "image/jpeg");

		assertThat(storage.fetchBytes("k1")).containsExactly(data);
	}

	@Test
	void fetch_unknownKey_throws() {
		InMemoryStorage storage = new InMemoryStorage("bucket-1");

		assertThatThrownBy(() -> storage.fetchBytes("missing"))
			.isInstanceOf(NoSuchElementException.class);
	}

	@Test
	void presignPut_returnsMockS3Url() {
		InMemoryStorage storage = new InMemoryStorage("bucket-x");

		String url = storage.presignPut("uploads/image/u/1.jpg", "image/jpeg", 600);

		assertThat(url).startsWith("mock-s3://bucket-x/uploads/image/u/1.jpg?op=put");
		assertThat(url).contains("ct=image/jpeg");
		assertThat(url).contains("sig=mock-deterministic");
	}

	@Test
	void presignGet_omitsContentType() {
		InMemoryStorage storage = new InMemoryStorage("bucket-x");

		String url = storage.presignGet("path", 600);

		assertThat(url).contains("op=get");
		assertThat(url).doesNotContain("ct=");
	}

	@Test
	void reset_clearsAllObjects() {
		InMemoryStorage storage = new InMemoryStorage("bucket-1");
		storage.putBytes("k", new byte[]{1}, "image/png");

		storage.reset();

		assertThatThrownBy(() -> storage.fetchBytes("k"))
			.isInstanceOf(NoSuchElementException.class);
	}
}
