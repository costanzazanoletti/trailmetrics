package com.trailmetrics.activities.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.util.List;
import java.util.Map;

@Service
public class StravaClient {

  @Value("${strava.api.base-url}")
  private String stravaBaseUrl;

  private final RestTemplate restTemplate;

  public StravaClient(RestTemplate externalRestTemplate) {
    this.restTemplate = externalRestTemplate;
  }

  public List<Map<String, Object>> fetchUserActivities(String accessToken) {
    String url = stravaBaseUrl + "/athlete/activities";

    HttpHeaders headers = new HttpHeaders();
    headers.setBearerAuth(accessToken);

    HttpEntity<Void> requestEntity = new HttpEntity<>(headers);
    ResponseEntity<List> response = restTemplate.exchange(
        url, HttpMethod.GET, requestEntity, List.class);

    return response.getBody();
  }
}
