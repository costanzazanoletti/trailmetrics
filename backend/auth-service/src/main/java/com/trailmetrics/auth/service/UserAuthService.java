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
  private final Map<String, String> refreshTokens = new ConcurrentHashMap<>();
  private final Map<String, Long> tokenExpiryTimes = new ConcurrentHashMap<>();

  private final TextEncryptor textEncryptor;
  private final StravaApiService stravaApiService;

  public UserAuthService(@Value("${app.encryption.secret-key}") String secretKey,
      @Value("${app.encryption.salt}") String salt, StravaApiService stravaApiService) {
    this.textEncryptor = Encryptors.text(secretKey, salt);
    this.stravaApiService = stravaApiService;
  }

  public String getStravaAccessToken(String userId) {
    String encryptedToken = userTokens.get(userId);
    if (encryptedToken == null) {
      return null;
    }
    if (isTokenExpired(userId)) {
      return refreshStravaAccessToken(userId);
    }
    return encryptedToken;
  }

  private String refreshStravaAccessToken(String userId) {
    String refreshToken = refreshTokens.get(userId);
    if (refreshToken == null) {
      return null;
    }
    StravaApiService.StravaTokenResponse newToken = stravaApiService.refreshAccessToken(
        refreshToken);
    storeStravaAccessToken(userId, newToken.accessToken, newToken.refreshToken, newToken.expiresIn);
    return getStravaAccessToken(userId);
  }

  public void storeStravaAccessToken(String userId, String accessToken, String refreshToken,
      long expiresIn) {
    // Store encrypted access token
    String encryptedToken = textEncryptor.encrypt(accessToken);
    userTokens.put(userId, encryptedToken);
    // Store expiry time in milliseconds
    long expiryTimeInMillis = System.currentTimeMillis() + (expiresIn * 1000L);
    tokenExpiryTimes.put(userId, expiryTimeInMillis);
    // Store refresh token
    refreshTokens.put(userId, refreshToken);
  }

  private boolean isTokenExpired(String userId) {
    Long expiryTimeInMillis = tokenExpiryTimes.get(userId);
    if (expiryTimeInMillis == null) {
      return true;
    }
    // Return if the token is expired or about to expire (5 seconds)
    return System.currentTimeMillis() >= expiryTimeInMillis + 5000L;
  }
}
