package com.petfinect.api.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.User;

/**
 * Spring Data JPA Repository 패턴.
 *
 * <p>{@link JpaRepository} 만 상속하면 다음이 자동 제공:
 * <ul>
 *   <li>{@code save / saveAll / findById / findAll / delete / deleteById / count / existsById}</li>
 *   <li>findBy{Field} 시그니처로 자동 쿼리 derivation
 *       (예: {@link #findByKakaoId(String)} → {@code SELECT * FROM "user" WHERE kakao_id=?})</li>
 * </ul>
 *
 * <p>복잡한 쿼리는 {@code @Query("SELECT ...")} JPQL 또는 native SQL 사용.
 */
@Repository
public interface UserRepository extends JpaRepository<User, UUID> {

	Optional<User> findByKakaoId(String kakaoId);

	boolean existsByKakaoId(String kakaoId);
}
