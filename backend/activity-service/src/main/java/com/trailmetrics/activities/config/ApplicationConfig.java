package com.trailmetrics.activities.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;


@Configuration
@Slf4j
public class ApplicationConfig {


  @Value("${auth-service.api-key}")
  private String apiKey;

  @Bean
  public RestTemplate internalRestTemplate() {
    RestTemplate restTemplate = new RestTemplate();
    restTemplate.getInterceptors().add((request, body, execution) -> {
      log.info("Adding API Key Header: {}", apiKey);
      request.getHeaders().add("X-API-KEY", apiKey);
      return execution.execute(request, body);
    });
    return restTemplate;
  }

  @Bean
  public RestTemplate externalRestTemplate() { // Used for calling Strava API
    return new RestTemplate();
  }

}
