package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.ActivityStream;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivityStreamRepository extends JpaRepository<ActivityStream, Long> {

  /**
   * Deletes all streams associated with a given activity.
   */
  void deleteByActivityId(Long activityId);
}
