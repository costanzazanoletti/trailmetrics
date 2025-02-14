package com.trailmetrics.auth.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

@Service
public class StravaApiService {

  private final RestTemplate restTemplate = new RestTemplate();
  private final ObjectMapper objectMapper = new ObjectMapper();

  @Value("${spring.security.oauth2.client.registration.strava.client-id}")
  private String clientId;

  @Value("${spring.security.oauth2.client.registration.strava.client-secret}")
  private String clientSecret;

  @Value("${external-api.strava.refresh-token-url}")
  private String refreshTokenUrl;


  public StravaTokenResponse refreshAccessToken(String refreshToken) {
    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

    MultiValueMap<String, String> requestBody = new LinkedMultiValueMap<>();
    requestBody.add("client_id", clientId);
    requestBody.add("client_secret", clientSecret);
    requestBody.add("refresh_token", refreshToken);
    requestBody.add("grant_type", "refresh_token");

    HttpEntity<MultiValueMap<String, String>> requestEntity = new HttpEntity<>(requestBody,
        headers);

    try {
      String response = restTemplate.postForObject(refreshTokenUrl, requestEntity, String.class);
      JsonNode jsonNode = objectMapper.readTree(response);

      return new StravaTokenResponse(
          jsonNode.get("access_token").asText(),
          jsonNode.get("refresh_token").asText(),
          jsonNode.get("expires_in").asLong()
      );

    } catch (Exception e) {
      throw new RuntimeException("Failed to refresh Strava access token", e);
    }
  }

  public static class StravaTokenResponse {

    public final String accessToken;
    public final String refreshToken;
    public final long expiresIn;

    public StravaTokenResponse(String accessToken, String refreshToken, long expiresIn) {
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      this.expiresIn = expiresIn;
    }
  }
}
