package com.trailmetrics.activities.service;

import com.trailmetrics.activities.exception.ResourceNotFoundException;
import com.trailmetrics.activities.exception.UnauthorizedAccessException;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@RequiredArgsConstructor
@Service
public class ActivityService {

  private final ActivityRepository activityRepository;
  private final ActivityStreamRepository activityStreamRepository;
  private final SegmentRepository segmentRepository;

  public Page<Activity> fetchUserActivities(Long userId, Pageable pageable) {
    return activityRepository.findByAthleteId(userId, pageable);
  }

  public Activity getUserActivityById(Long activityId, Long userId) {
    Activity activity = activityRepository.findById(activityId)
        .orElseThrow(() -> new ResourceNotFoundException("Activity not found"));
    if (!activity.getAthleteId().equals(userId)) {
      throw new UnauthorizedAccessException("User unauthorized to view this activity");
    }

    return activity;
  }

  public List<ActivityStream> getActivityStreams(Long activityId) {
    return activityStreamRepository.findByActivityId(activityId);
  }

  public List<Segment> getActivitySegments(Long id) {
    return segmentRepository.findByActivityId(id);
  }
}
