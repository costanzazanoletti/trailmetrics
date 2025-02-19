package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.Activity;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ActivityRepository extends JpaRepository<Activity, Long> {

  /**
   * Finds all activities for a given athlete ID.
   */
  List<Activity> findByAthleteId(Long athleteId);
}
