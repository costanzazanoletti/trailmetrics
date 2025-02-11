package com.trailmetrics.activities.config;


import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

@Configuration
public class ApplicationConfig {

  @Value("${auth-service.api-key}")
  private String apiKey;

  @Bean
  public RestTemplate restTemplate() {
    return AuthServiceInterceptor.createRestTemplate(apiKey);
  }
}

