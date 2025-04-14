package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.Activity;
import java.util.Set;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ActivityRepository extends JpaRepository<Activity, Long> {


  /**
   * Finds all activity ids for a given athlete ID.
   */
  Set<Long> findActivityIdsByAthleteId(Long userId);

  /**
   * Deletes activities by id
   */
  void deleteByIdIn(Set<Long> ids);
}
