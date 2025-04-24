package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.ActivityStream;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivityStreamRepository extends JpaRepository<ActivityStream, Long> {

  int countByActivityId(Long activityId);

  List<ActivityStream> findByActivityId(Long activityId);
}
