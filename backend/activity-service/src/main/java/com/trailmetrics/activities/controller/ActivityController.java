package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.security.JwtUtils;
import io.jsonwebtoken.Claims;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/activities")
public class ActivityController {

  private final StravaClient stravaClient;
  private final JwtUtils jwtUtils;

  public ActivityController(StravaClient stravaClient, JwtUtils jwtUtils) {
    this.stravaClient = stravaClient;
    this.jwtUtils = jwtUtils;
  }

  @GetMapping
  public ResponseEntity<List<Map<String, Object>>> getActivities(@RequestHeader("Authorization") String authHeader) {
    String token = authHeader.replace("Bearer ", "");
    Claims claims = jwtUtils.parseToken(token);

    String userId = claims.getSubject(); // Get Strava user ID from JWT
    String accessToken = ""; // TODO: Retrieve access token for this user from database

    List<Map<String, Object>> activities = stravaClient.fetchUserActivities(accessToken);
    return ResponseEntity.ok(activities);
  }
}
