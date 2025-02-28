package com.trailmetrics.auth.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import io.jsonwebtoken.Claims;
import jakarta.annotation.PostConstruct;
import java.security.PublicKey;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest(properties = {
    "spring.config.location=classpath:/application-test.yml"
})
@ActiveProfiles("test")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class JwtUtilsTest {


  @Value("${jwt.expiration-time}")
  private long EXPIRATION_TIME;

  @PostConstruct
  public void init() {
    System.out.println("Loaded JWT Expiration Time: " + EXPIRATION_TIME);
  }

  @Autowired
  private JwtUtils jwtUtils;


  @Test
  void testGenerateAndParseToken() {
    String userId = "testuser";

    // Generate a token
    String token = jwtUtils.generateToken(userId);
    assertNotNull(token);
    System.out.println("Generated Token: " + token);

    // Parse the token
    Claims claims = jwtUtils.parseToken(token);
    assertNotNull(claims);
    assertEquals(userId, claims.getSubject());
  }

  @Test
  void testTokenExpiration() {
    String token = jwtUtils.generateToken("testuser");

    // Ensure token is initially valid
    assertTrue(jwtUtils.isTokenValid(token));

    // Wait for expiration
    try {
      Thread.sleep(3000); // Wait 6 seconds (longer than 2s expiration in application-test.yml)
    } catch (InterruptedException e) {
      e.printStackTrace();
    }

    // Now the token should be invalid
    assertFalse(jwtUtils.isTokenValid(token));
  }

  @Test
  void testPublicKeyExposure() {
    PublicKey publicKey = jwtUtils.getPublicKey();
    assertNotNull(publicKey);
    System.out.println("Public Key: " + publicKey);
  }
}
