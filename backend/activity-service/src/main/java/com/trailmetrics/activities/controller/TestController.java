package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.dto.ActivityStreamDTO;
import com.trailmetrics.activities.service.ActivitySyncService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/test")
@RequiredArgsConstructor
public class TestController {

  private final ActivitySyncService activitySyncService;
  private final StravaClient stravaClient;

  @GetMapping("/activities")
  public String getActivities(HttpServletRequest request) {

    String userId = request.getParameter("userId");

    String accessToken = request.getParameter("accessToken");

    activitySyncService.syncUserActivities(userId, accessToken);
    return "Started sync";
  }

  @GetMapping("/activity/details")
  public ActivityDTO getActivityDetails(HttpServletRequest request) {
    String accessToken = request.getParameter("accessToken");
    String activityId = request.getParameter("id");
    ActivityDTO activity = stravaClient.fetchActivityDetails(accessToken,
        Long.parseLong(activityId));
    return activity;
  }

  @GetMapping("/activity/stream")
  public ActivityStreamDTO getActivityStream(HttpServletRequest request) {
    String accessToken = request.getParameter("accessToken");
    String activityId = request.getParameter("id");
    ActivityStreamDTO activityStream = stravaClient.fetchActivityStream(accessToken,
        Long.parseLong(activityId));
    return activityStream;
  }
}
