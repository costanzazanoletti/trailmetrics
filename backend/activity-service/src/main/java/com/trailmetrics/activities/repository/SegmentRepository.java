package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.Segment;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SegmentRepository extends JpaRepository<Segment, Long> {

  List<Segment> findByActivityId(Long activityId);

}
