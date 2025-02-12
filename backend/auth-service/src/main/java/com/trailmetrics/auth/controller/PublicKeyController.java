package com.trailmetrics.auth.controller;

import com.trailmetrics.auth.security.JwtUtils;
import java.security.PublicKey;
import java.util.Base64;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal")
public class PublicKeyController {

  private final JwtUtils jwtUtils;

  public PublicKeyController(JwtUtils jwtUtils) {
    this.jwtUtils = jwtUtils;
  }

  @GetMapping("/public-key")
  public String getPublicKey() {
    PublicKey publicKey = jwtUtils.getPublicKey();
    return "-----BEGIN PUBLIC KEY-----\n"
        + Base64.getEncoder().encodeToString(publicKey.getEncoded())
        + "\n-----END PUBLIC KEY-----";
  }
}
