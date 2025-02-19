package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.ActivityStream;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivityStreamRepository extends JpaRepository<ActivityStream, Long> {

  /**
   * Finds all streams for a given activity.
   */
  List<ActivityStream> findByActivityId(Long activityId);
}
