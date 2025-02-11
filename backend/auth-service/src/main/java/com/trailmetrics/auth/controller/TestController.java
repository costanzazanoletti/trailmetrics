package com.trailmetrics.auth.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal")
public class TestController {

  @GetMapping("/test")
  public String testApiKey() {
    return "Auth-Service API Key authentication successful!";
  }
}
