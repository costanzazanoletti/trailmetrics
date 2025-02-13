package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.security.JwtUtils;
import com.trailmetrics.activities.service.ActivityService;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/activities")
public class ActivityController {

  private final StravaClient stravaClient;
  private final JwtUtils jwtUtils;
  private final ActivityService activityService;

  public ActivityController(StravaClient stravaClient, JwtUtils jwtUtils, ActivityService activityService) {
    this.stravaClient = stravaClient;
    this.jwtUtils = jwtUtils;
    this.activityService = activityService;
  }

  @GetMapping
  public ResponseEntity<?> getUserActivities(HttpServletRequest request) {


    //List<Activity> activities = activityService.getActivitiesByUserId(userId);
    return ResponseEntity.ok("List of activities");
  }
}
