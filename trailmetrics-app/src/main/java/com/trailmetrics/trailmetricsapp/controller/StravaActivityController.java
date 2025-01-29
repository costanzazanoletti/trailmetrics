package com.trailmetrics.trailmetricsapp.controller;

import com.trailmetrics.trailmetricsapp.model.Activity;
import com.trailmetrics.trailmetricsapp.service.StravaActivityService;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/activities")
public class StravaActivityController {

  private final StravaActivityService stravaActivityService;
  private final AtomicBoolean syncInProgress = new AtomicBoolean(false);

  public StravaActivityController(StravaActivityService stravaActivityService) {
    this.stravaActivityService = stravaActivityService;
  }

  @GetMapping("/sync")
  public List<Activity> syncActivities(OAuth2AuthenticationToken authentication) {
    syncInProgress.set(true);
    new Thread(() -> {
      stravaActivityService.fetchAndSaveActivities(authentication);
      syncInProgress.set(false);
    }).start();
    return List.of();
  }

  @GetMapping("/status")
  public SyncStatus getSyncStatus() {
    return new SyncStatus(!syncInProgress.get());
  }

  private record SyncStatus(boolean completed) {

  }
}
