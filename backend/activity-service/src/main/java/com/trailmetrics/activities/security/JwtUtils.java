package com.trailmetrics.activities.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.JwtException;
import java.util.Date;
import org.springframework.stereotype.Component;

import java.security.PublicKey;

@Component
public class JwtUtils {

  private final JwtPublicKeyProvider publicKeyProvider;

  public JwtUtils(JwtPublicKeyProvider publicKeyProvider) {
    this.publicKeyProvider = publicKeyProvider;
  }

  public Claims parseToken(String token) {
    try {
      PublicKey publicKey = publicKeyProvider.getPublicKey();
      return Jwts.parser()
          .setSigningKey(publicKey)
          .build()
          .parseClaimsJws(token)
          .getBody();
    } catch (JwtException e) {
      throw new RuntimeException("Invalid JWT token", e);
    }
  }

  public boolean isTokenValid(String token) {
    try {
      Claims claims =   parseToken(token);
      return claims.getExpiration().after(new Date());

    } catch (Exception e) {
      return false;
    }
  }

  public String extractUsername(String token) {
    Claims claims = parseToken(token);
    return claims.getSubject();
  }
}
