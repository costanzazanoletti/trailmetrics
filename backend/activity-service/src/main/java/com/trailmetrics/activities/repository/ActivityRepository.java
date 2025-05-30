package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.Activity;
import java.util.Set;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

@Repository
public interface ActivityRepository extends JpaRepository<Activity, Long> {

  @Query("select a.id from Activity a where a.athleteId = :athleteId and a.isPlanned = false")
  Set<Long> findActivityIdsByAthleteId(Long athleteId);

  void deleteByIdIn(Set<Long> ids);

  Page<Activity> findByAthleteIdAndIsPlannedIsFalseOrIsPlannedIsNull(Long athleteId,
      Pageable pageable);

  Page<Activity> findByAthleteIdAndIsPlannedIsTrue(Long athleteId, Pageable pageable);

}
