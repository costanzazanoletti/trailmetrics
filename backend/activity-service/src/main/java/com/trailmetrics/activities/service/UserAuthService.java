package com.trailmetrics.activities.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.encrypt.Encryptors;
import org.springframework.security.crypto.encrypt.TextEncryptor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Service
public class UserAuthService {

  @Value("${auth-service.url}")
  private String authServiceUrl;
  private final RestTemplate internalRestTemplate;

  private final TextEncryptor textEncryptor;

  public UserAuthService(@Value("${app.encryption.secret-key}") String secretKey,
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
    String encryptedToken = internalRestTemplate.getForObject(url, String.class);
    return textEncryptor.decrypt(encryptedToken);
  }
}
