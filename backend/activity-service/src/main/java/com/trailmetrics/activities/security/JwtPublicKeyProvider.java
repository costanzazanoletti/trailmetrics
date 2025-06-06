package com.trailmetrics.activities.security;

import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
@Slf4j
public class JwtPublicKeyProvider {


  private final String authServicePublicKeyUrl;
  private final RestTemplate restTemplate;
  private PublicKey cachedPublicKey; // Cached key to avoid frequent requests

  public JwtPublicKeyProvider(RestTemplate internalRestTemplate,
      @Value("${auth-service.public-key-url}") String authServicePublicKeyUrl) {
    this.restTemplate = internalRestTemplate;
    this.authServicePublicKeyUrl = authServicePublicKeyUrl;
    refreshPublicKey(); // Retrieve the key at startup
  }

  public void refreshPublicKey() {
    try {
      log.info("Requesting public key from auth-service at {}", authServicePublicKeyUrl);

      ResponseEntity<String> response = restTemplate.getForEntity(authServicePublicKeyUrl,
          String.class);

      if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
        cachedPublicKey = convertPemToPublicKey(response.getBody());
        log.info("Retrieved public key{}", cachedPublicKey);
      } else {
        log.error("Failed to retrieve public key: {}", response.getStatusCode());
      }
    } catch (Exception e) {
      log.error("Exception while fetching public key from auth-service", e);
    }
  }

  public PublicKey getPublicKey() {
    return cachedPublicKey;
  }

  private PublicKey convertPemToPublicKey(String pem) throws Exception {
    String publicKeyPEM = pem.replace("-----BEGIN PUBLIC KEY-----", "")
        .replace("-----END PUBLIC KEY-----", "")
        .replaceAll("\\s", "");

    byte[] decodedKey = Base64.getDecoder().decode(publicKeyPEM);
    X509EncodedKeySpec keySpec = new X509EncodedKeySpec(decodedKey);
    return KeyFactory.getInstance("RSA").generatePublic(keySpec);
  }
}
