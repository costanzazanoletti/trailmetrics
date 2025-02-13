package com.trailmetrics.auth.controller;

import com.trailmetrics.auth.service.UserAuthService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/user-auth")
public class UserAuthController {

  private final UserAuthService userAuthService;

  public UserAuthController(UserAuthService userAuthService) {
    this.userAuthService = userAuthService;
  }

  @GetMapping("/access-token")
  public ResponseEntity<?> getAccessToken(HttpServletRequest request) {
    String userId = (String) request.getParameter("userId");

    if (userId == null) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Unauthorized");
    }

    String accessToken = userAuthService.getStravaAccessToken(userId);
    if (accessToken == null) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Access token not found");
    }

    return ResponseEntity.status(HttpStatus.OK).body(accessToken);
  }
}
