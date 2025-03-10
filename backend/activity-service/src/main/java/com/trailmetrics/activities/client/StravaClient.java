package com.trailmetrics.activities.client;

import com.trailmetrics.activities.dto.ActivityDTO;
import java.io.IOException;
import java.io.InputStream;
import java.time.Instant;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.Resource;
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
    UriComponentsBuilder uriBuilder = UriComponentsBuilder.fromUriString(
            stravaBaseUrl + "/athlete/activities")
        .queryParam("before", before.getEpochSecond())
        .queryParam("after", after.getEpochSecond())
        .queryParam("page", page)
        .queryParam("per_page", maxPerPage);

    HttpEntity<Void> requestEntity = getVoidHttpEntity(accessToken, uriBuilder);

    ResponseEntity<List<ActivityDTO>> response = restTemplate.exchange(
        uriBuilder.toUriString(),
        HttpMethod.GET,
        requestEntity,
        new ParameterizedTypeReference<>() {
        }
    );

    return response.getBody();
  }

  /*public ActivityDTO fetchActivityDetails(String accessToken, Long activityId) {
    UriComponentsBuilder uriBuilder = UriComponentsBuilder.fromUriString(
        stravaBaseUrl + "/activities/" + activityId);

    HttpEntity<Void> requestEntity = getVoidHttpEntity(accessToken, uriBuilder);

    ResponseEntity<ActivityDTO> response = restTemplate.exchange(
        uriBuilder.toUriString(),
        HttpMethod.GET,
        requestEntity,
        ActivityDTO.class
    );
    return response.getBody();
  }*/

  public InputStream fetchActivityStream(String accessToken, Long activityId) {
    UriComponentsBuilder uriBuilder = UriComponentsBuilder.fromUriString(
            stravaBaseUrl + "/activities/" + activityId + "/streams")
        .queryParam("keys",
            "time,distance,latlng,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth")
        .queryParam("key_by_type", "true");

    HttpEntity<Void> requestEntity = getVoidHttpEntity(accessToken, uriBuilder);

    ResponseEntity<Resource> response = restTemplate.exchange(
        uriBuilder.toUriString(),
        HttpMethod.GET,
        requestEntity,
        Resource.class
    );

    if (response.getBody() != null) {
      try {
        return response.getBody().getInputStream();
      } catch (IOException e) {
        throw new RuntimeException("Error retrieving input stream from response", e);
      }
    } else {
      throw new RuntimeException("Empty response from Strava API");
    }
  }

  private static HttpEntity<Void> getVoidHttpEntity(String accessToken,
      UriComponentsBuilder uriBuilder) {
    HttpHeaders headers = new HttpHeaders();
    headers.setBearerAuth(accessToken);

    HttpEntity<Void> requestEntity = new HttpEntity<>(headers);

    log.info("Sending Request: [Method: GET] {}", uriBuilder.toUriString());
    log.info("Headers: {}", headers);
    return requestEntity;
  }


}
