package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.service.ActivitySyncService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/test")
public class TestController {

  private final ActivitySyncService activitySyncService;

  public TestController(ActivitySyncService activitySyncService) {
    this.activitySyncService = activitySyncService;
  }

  @GetMapping("/activities")
  public String getActivities(HttpServletRequest request) {

    String userId = request.getParameter("userId");

    String accessToken = request.getParameter("accessToken");

    activitySyncService.syncUserActivities(userId, accessToken);
    return "Started sync";
  }
}
