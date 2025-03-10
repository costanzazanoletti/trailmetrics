package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.service.AuthServiceClient;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth-service")
public class AuthServiceController {

  private final AuthServiceClient authServiceClient;

  public AuthServiceController(AuthServiceClient authServiceClient) {
    this.authServiceClient = authServiceClient;
  }

}
