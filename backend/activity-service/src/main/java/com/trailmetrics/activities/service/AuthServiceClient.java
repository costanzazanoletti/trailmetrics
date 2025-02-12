package com.trailmetrics.activities.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class AuthServiceClient {

  private final RestTemplate restTemplate;
  private final String authServiceUrl;

  public AuthServiceClient(RestTemplate restTemplate, @Value("${auth-service.url}") String authServiceUrl) {
    this.restTemplate = restTemplate;
    this.authServiceUrl = authServiceUrl;
  }


  public String getPublicKey(){
    return restTemplate.getForObject(authServiceUrl + "/internal/public-key", String.class);
  }
}
