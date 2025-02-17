package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.service.ActivitySyncService;
import com.trailmetrics.activities.service.UserAuthService;
import jakarta.servlet.http.HttpServletRequest;
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
  public ResponseEntity<List<Activity>> getActivities(HttpServletRequest request) {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    String userId = authentication.getName();
    List<Activity> activities = new ArrayList<>();

    if (authentication == null || !authentication.isAuthenticated()) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }
    String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

    activitySyncService.syncUserActivities(userId, accessToken);

    return ResponseEntity.ok(activities);
  }
}
