package com.petfinect.api.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.NotificationLog;

@Repository
public interface NotificationLogRepository extends JpaRepository<NotificationLog, UUID> {

	List<NotificationLog> findByUserIdOrderBySentAtDesc(UUID userId, Pageable pageable);
}
