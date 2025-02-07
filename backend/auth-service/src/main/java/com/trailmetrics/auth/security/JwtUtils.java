package com.trailmetrics.auth.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import java.security.Key;
import java.time.Instant;
import java.util.Date;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class JwtUtils {

  @Value("${jwt.secret-key}")
  private String SECRET_KEY;
  @Value("${jwt.expiration-time}")
  private long EXPIRATION_TIME;

  private Key getSigningKey() {
    return Keys.hmacShaKeyFor(Decoders.BASE64.decode(SECRET_KEY));
  }

  public String generateToken(String userId) {
    Instant now = Instant.now();
    Instant expiration = now.plusSeconds(EXPIRATION_TIME);

    String jwt = Jwts.builder()
        .subject(userId)
        .issuedAt(Date.from(now))
        .expiration(Date.from(expiration))
        .signWith(getSigningKey(), SignatureAlgorithm.HS256)
        .compact();
    return jwt;
  }

  public Claims parseToken(String token) {
    return (Claims) Jwts.parser()
        .setSigningKey(getSigningKey())
        .build()
        .parseSignedClaims(token)
        .getPayload();
  }

  public boolean isTokenValid(String token) {
    try {
      Instant expirationTime = parseToken(token).getExpiration().toInstant();
      return expirationTime.isAfter(Instant.now());
    } catch (Exception e) {
      return false;
    }
  }
}
