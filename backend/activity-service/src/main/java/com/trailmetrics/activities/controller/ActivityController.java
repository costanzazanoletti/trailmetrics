package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.service.ActivityService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/activities")
public class ActivityController {


  private final ActivityService activityService;

  public ActivityController(ActivityService activityService) {

    this.activityService = activityService;
  }

  @GetMapping
  public ResponseEntity<List<Map<String, Object>>> getActivities(HttpServletRequest request) {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

    if (authentication == null || !authentication.isAuthenticated()) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }

    String userId = authentication.getName();

    List<Map<String, Object>> activities = activityService.getUserActivities(userId);
    return ResponseEntity.ok(activities);
  }
}
