package com.petfinect.api.repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.Meal;

@Repository
public interface MealRepository extends JpaRepository<Meal, UUID> {

	List<Meal> findByPetIdAndTsBetweenOrderByTsAsc(
		UUID petId, OffsetDateTime from, OffsetDateTime to);
}
