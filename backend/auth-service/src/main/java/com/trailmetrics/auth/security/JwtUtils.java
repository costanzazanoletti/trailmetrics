package com.trailmetrics.auth.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import jakarta.annotation.PostConstruct;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.time.Instant;
import java.util.Base64;
import java.util.Date;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

@Component
public class JwtUtils {

  @Value("${jwt.expiration-time}")
  private long EXPIRATION_TIME;

  private PrivateKey privateKey;
  private PublicKey publicKey;

  @PostConstruct
  public void init() {
    try {
      privateKey = loadPrivateKey("keys/private.pem");
      publicKey = loadPublicKey("keys/public.pem");
    } catch (Exception e) {

      throw new RuntimeException("Error loading RSA keys", e);
    }
  }

  public PublicKey getPublicKey() {
    return publicKey;
  }

  private PrivateKey loadPrivateKey(String path) throws Exception {

    String key = new String(new ClassPathResource(path).getInputStream().readAllBytes());
    key = key.replace("-----BEGIN PRIVATE KEY-----", "")
        .replace("-----END PRIVATE KEY-----", "")
        .replaceAll("\\s", ""); // Remove spaces

    byte[] decodedKey = Base64.getDecoder().decode(key);
    PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(decodedKey);
    return KeyFactory.getInstance("RSA").generatePrivate(keySpec);
  }

  private PublicKey loadPublicKey(String path) throws Exception {

    String key = new String(new ClassPathResource(path).getInputStream().readAllBytes());
    key = key.replace("-----BEGIN PUBLIC KEY-----", "")
        .replace("-----END PUBLIC KEY-----", "")
        .replaceAll("\\s", ""); // Remove spaces

    byte[] decodedKey = Base64.getDecoder().decode(key);
    X509EncodedKeySpec keySpec = new X509EncodedKeySpec(decodedKey);
    return KeyFactory.getInstance("RSA").generatePublic(keySpec);
  }

  public String generateToken(String userId) {
    Instant now = Instant.now();
    Instant expiration = now.plusSeconds(EXPIRATION_TIME);

    return Jwts.builder()
        .setSubject(userId)
        .setIssuedAt(Date.from(now))
        .setExpiration(Date.from(expiration))
        .signWith(privateKey, SignatureAlgorithm.RS256)
        .compact();
  }

  public Claims parseToken(String token) {
    return Jwts.parser()
        .setSigningKey(publicKey)
        .setAllowedClockSkewSeconds(1)
        .build()
        .parseClaimsJws(token)
        .getBody();
  }

  public boolean isTokenValid(String token) {
    try {
      Instant expirationTime = parseToken(token).getExpiration().toInstant();

      return expirationTime.isAfter(Instant.now());
    } catch (Exception e) {
      System.out.println("⚠ Token is invalid or expired.");
      return false;
    }
  }
}
