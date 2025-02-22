package com.trailmetrics.activities.service;

import com.trailmetrics.activities.exception.TrailmetricsAuthServiceException;
import java.util.Optional;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.encrypt.Encryptors;
import org.springframework.security.crypto.encrypt.TextEncryptor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Service
@Slf4j
public class UserAuthService {


  @Value("${auth-service.url}")
  private String authServiceUrl;
  private final RestTemplate internalRestTemplate;

  private final TextEncryptor textEncryptor;

  public UserAuthService(
      @Value("${app.encryption.secret-key}") String secretKey,
      @Value("${app.encryption.salt}") String salt,
      RestTemplate internalRestTemplate) {
    this.internalRestTemplate = internalRestTemplate;
    this.textEncryptor = Encryptors.text(secretKey, salt);
  }

  public String fetchAccessTokenFromAuthService(String userId) {
    String url = UriComponentsBuilder.fromUriString(
            authServiceUrl + "/internal/user-auth/access-token")
        .queryParam("userId", userId)
        .toUriString();
    try {
      String encryptedToken = internalRestTemplate.getForObject(url, String.class);
      return Optional.ofNullable(encryptedToken).map(textEncryptor::decrypt)
          .orElseThrow(() -> new RuntimeException("Received null token from Auth Service"));
    } catch (HttpClientErrorException.Unauthorized e) {
      log.error("Unauthorized: Invalid user credentials or token expired for userId={}", userId);
      throw new TrailmetricsAuthServiceException(
          "Unauthorized request: Access token is invalid or expired.");
    } catch (ResourceAccessException e) {
      log.error("Auth Service is unreachable: {}", e.getMessage());
      throw new TrailmetricsAuthServiceException(
          "Auth Service is unavailable. Please try again later.");
    } catch (Exception e) {
      log.error("Unexpected error while fetching token: {}", e.getMessage());
      throw new TrailmetricsAuthServiceException("Failed to retrieve valid Strava access token");
    }
  }
}
