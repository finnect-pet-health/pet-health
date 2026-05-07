package com.petfinect.api.repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.petfinect.api.domain.CalendarTask;

@Repository
public interface CalendarTaskRepository extends JpaRepository<CalendarTask, UUID> {

	List<CalendarTask> findByFamilyIdAndDueAtBetweenOrderByDueAtAsc(
		UUID familyId, OffsetDateTime from, OffsetDateTime to);
}
