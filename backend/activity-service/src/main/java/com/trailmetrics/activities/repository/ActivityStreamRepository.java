package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.ActivityStream;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivityStreamRepository extends JpaRepository<ActivityStream, Long> {
  
  /**
   * Counts streams associated with a given activity.
   */
  int countByActivityId(Long activityId);
}
