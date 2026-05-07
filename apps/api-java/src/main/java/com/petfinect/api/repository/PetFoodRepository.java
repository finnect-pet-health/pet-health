package com.petfinect.api.repository;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.PetFood;

@Repository
public interface PetFoodRepository extends JpaRepository<PetFood, UUID> {

	List<PetFood> findByBrandContainingIgnoreCase(String brand);

	List<PetFood> findByNameContainingIgnoreCase(String name);
}
