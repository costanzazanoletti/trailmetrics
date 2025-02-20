package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.service.ActivitySyncService;
import com.trailmetrics.activities.service.UserAuthService;
import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/activities")
@RequiredArgsConstructor
public class ActivityController {


  private final ActivitySyncService activitySyncService;
  private final UserAuthService userAuthService;


  @GetMapping
  public ResponseEntity<List<Activity>> getActivities() {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    if (authentication == null || !authentication.isAuthenticated()) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }

    String userId = authentication.getName();
    List<Activity> activities = new ArrayList<>();

    String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);
    // Synchronize Strava activities
    activitySyncService.syncUserActivities(userId, accessToken);

    return ResponseEntity.ok(activities);
  }
}
