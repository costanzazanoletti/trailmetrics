package com.trailmetrics.auth.service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.encrypt.Encryptors;
import org.springframework.security.crypto.encrypt.TextEncryptor;
import org.springframework.stereotype.Service;

@Service
public class UserAuthService {

  private final Map<String, String> userTokens = new ConcurrentHashMap<>();
  private final TextEncryptor textEncryptor;

  public UserAuthService(@Value("${app.encryption.secret-key}") String secretKey,
      @Value("${app.encryption.salt}") String salt) {
    this.textEncryptor = Encryptors.text(secretKey, salt);
  }

  public String getStravaAccessToken(String userId) {
    return userTokens.get(userId);
  }

  public void storeStravaAccessToken(String userId, String accessToken) {
    String encryptedToken = textEncryptor.encrypt(accessToken);
    userTokens.put(userId, encryptedToken);
  }
}
