package com.petfinect.api.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.Device;

@Repository
public interface DeviceRepository extends JpaRepository<Device, UUID> {

	Optional<Device> findByExpoToken(String expoToken);

	List<Device> findByUserId(UUID userId);
}
