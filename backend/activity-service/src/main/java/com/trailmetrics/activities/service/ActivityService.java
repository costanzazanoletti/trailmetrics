package com.trailmetrics.activities.service;

import com.trailmetrics.activities.client.StravaClient;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class ActivityService {


  private final StravaClient stravaClient;

  private final UserAuthService userAuthService;

  public ActivityService(StravaClient stravaClient, UserAuthService userAuthService) {
    this.stravaClient = stravaClient;
    this.userAuthService = userAuthService;

  }

  public List<Map<String, Object>> getUserActivities(String userId) {
    String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

    if (accessToken != null) {
      return stravaClient.fetchUserActivities(accessToken);
    } else {
      throw new RuntimeException("Failed to retrieve Strava access token");
    }
  }


}
