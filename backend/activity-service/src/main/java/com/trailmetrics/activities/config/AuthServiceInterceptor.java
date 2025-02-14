package com.trailmetrics.activities.config;

import java.io.IOException;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.InterceptingClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Slf4j
public class AuthServiceInterceptor implements ClientHttpRequestInterceptor {


  private final String apiKey;

  public AuthServiceInterceptor(String apiKey) {
    this.apiKey = apiKey;
  }

  @Override
  public org.springframework.http.client.ClientHttpResponse intercept(
      org.springframework.http.HttpRequest request,
      byte[] body,
      ClientHttpRequestExecution execution) throws IOException {
    // Add API Key to request headers
    request.getHeaders().add("X-API-KEY", apiKey);

    // Log request details
    log.info("Outgoing request to: {}", request.getURI());
    log.info("Request Headers: {}", request.getHeaders());

    return execution.execute(request, body);
  }

  // Factory method to create RestTemplate with interceptor
  public static RestTemplate createRestTemplate(String apiKey) {
    RestTemplate restTemplate = new RestTemplate();
    ClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();

    // Add the interceptor that appends the API Key to all requests
    restTemplate.setRequestFactory(new InterceptingClientHttpRequestFactory(factory,
        List.of(new AuthServiceInterceptor(apiKey))));
    return restTemplate;
  }
}

