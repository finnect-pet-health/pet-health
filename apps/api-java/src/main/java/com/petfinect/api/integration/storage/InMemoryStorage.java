package com.petfinect.api.integration.storage;

import java.time.Instant;
import java.util.NoSuchElementException;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 학습/테스트 전용 in-memory storage.
 *
 * <h3>운영 부적합</h3>
 * <ul>
 *   <li>인스턴스 재시작 시 모든 객체 손실.</li>
 *   <li>프로세스 메모리 사용 — 큰 파일 다수면 OOM.</li>
 *   <li>다중 인스턴스 간 공유 안 됨.</li>
 * </ul>
 *
 * <h3>presign URL 형식</h3>
 * <p>{@code mock-s3://{bucket}/{key}?op={put|get}&expires={ts}&ct={contentType}&sig=mock-deterministic}
 * — Python 과 동일. 모바일 helper 가 이 스킴을 인식하면 dev 모드에서 forward 가능.
 */
public class InMemoryStorage implements StorageProvider {

	private final String bucket;
	private final ConcurrentHashMap<String, Entry> objects = new ConcurrentHashMap<>();

	public InMemoryStorage(String bucket) {
		this.bucket = bucket;
	}

	@Override
	public String presignPut(String key, String contentType, int ttlSeconds) {
		return buildUrl(key, contentType, ttlSeconds, "put");
	}

	@Override
	public String presignGet(String key, int ttlSeconds) {
		return buildUrl(key, "", ttlSeconds, "get");
	}

	@Override
	public byte[] fetchBytes(String key) {
		Entry entry = objects.get(key);
		if (entry == null) {
			throw new NoSuchElementException("object not found: " + key);
		}
		return entry.data();
	}

	@Override
	public void putBytes(String key, byte[] data, String contentType) {
		objects.put(key, new Entry(data, contentType));
	}

	public void reset() {
		objects.clear();
	}

	private String buildUrl(String key, String contentType, int ttlSeconds, String op) {
		long expires = Instant.now().getEpochSecond() + ttlSeconds;
		String ctPart = contentType.isEmpty() ? "" : "&ct=" + contentType;
		return "mock-s3://" + bucket + "/" + key
			+ "?op=" + op + "&expires=" + expires + ctPart + "&sig=mock-deterministic";
	}

	private record Entry(byte[] data, String contentType) {}
}
