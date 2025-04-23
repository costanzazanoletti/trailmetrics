package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.repository.ActivityRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@RequiredArgsConstructor
@Service
public class ActivityService {

  private final ActivityRepository activityRepository;

  public Page<Activity> fetchUserActivities(Long userId, Pageable pageable) {
    return activityRepository.findByAthleteId(userId, pageable);
  }
}
