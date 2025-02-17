package com.trailmetrics.activities.client;

import com.trailmetrics.activities.dto.ActivityDTO;
import java.time.Instant;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Service
@Slf4j
public class StravaClient {

  @Value("${strava.api.base-url}")
  private String stravaBaseUrl;

  private final RestTemplate restTemplate;

  public StravaClient(RestTemplate externalRestTemplate) {
    this.restTemplate = externalRestTemplate;
  }

  public List<ActivityDTO> fetchUserActivities(String accessToken, Instant before,
      Instant after, int page, int maxPerPage) {
    UriComponentsBuilder uriBuilder = UriComponentsBuilder.fromHttpUrl(
            stravaBaseUrl + "/athlete/activities")
        .queryParam("before", before.getEpochSecond())
        .queryParam("after", after.getEpochSecond())
        .queryParam("page", page)
        .queryParam("per_page", maxPerPage);

    HttpHeaders headers = new HttpHeaders();
    headers.setBearerAuth(accessToken);

    HttpEntity<Void> requestEntity = new HttpEntity<>(headers);

    log.info("Sending Request: [Method: GET] {}", uriBuilder.toUriString());
    log.info("Headers: {}", headers);

    ResponseEntity<List<ActivityDTO>> response = restTemplate.exchange(
        uriBuilder.toUriString(),
        HttpMethod.GET,
        requestEntity,
        new ParameterizedTypeReference<List<ActivityDTO>>() {
        }
    );

    return response.getBody();
  }
}
