package com.trailmetrics.activities.service;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityDTO;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ActivityService {


  private final StravaClient stravaClient;
  private final UserAuthService userAuthService;

  public ActivityService(StravaClient stravaClient, UserAuthService userAuthService) {
    this.stravaClient = stravaClient;
    this.userAuthService = userAuthService;

  }

  public List<ActivityDTO> getUserActivities(String userId) {
    String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

    if (accessToken != null) {
      return stravaClient.fetchUserActivities(accessToken, Instant.now().minus(2, ChronoUnit.YEARS),
          Instant.now(), 1, 50);
    } else {
      throw new RuntimeException("Failed to retrieve Strava access token");
    }
  }


}
