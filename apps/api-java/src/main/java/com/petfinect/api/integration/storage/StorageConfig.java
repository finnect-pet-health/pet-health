package com.petfinect.api.integration.storage;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

/**
 * Storage 빈 분기.
 *
 * <p>현재는 production 환경에서도 InMemoryStorage 사용 (실 S3 구현 미완).
 * 본격 이행 시 {@code S3Storage} 추가 후 {@code @Profile("production")} 으로 swap.
 */
@Configuration
public class StorageConfig {

	@Bean
	@Profile("!s3-real")
	public StorageProvider inMemoryStorage(
		@Value("${petfinect.storage.bucket:petfinect-dev}") String bucket
	) {
		return new InMemoryStorage(bucket);
	}
}
