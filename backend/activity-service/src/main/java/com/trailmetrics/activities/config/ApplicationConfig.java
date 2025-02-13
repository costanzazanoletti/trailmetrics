package com.trailmetrics.activities.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;


@Configuration
public class ApplicationConfig {

  private final static Logger logger = LoggerFactory.getLogger(ApplicationConfig.class);

  @Value("${auth-service.api-key}")
  private String apiKey;

  @Bean
  public RestTemplate internalRestTemplate() {
    RestTemplate restTemplate = new RestTemplate();
    restTemplate.getInterceptors().add((request, body, execution) -> {
      logger.info("Adding API Key Header: {}", apiKey);
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
