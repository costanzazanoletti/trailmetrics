package com.trailmetrics.auth.controller;


import java.util.Map;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class OAuthController {

  private final OAuth2AuthorizedClientService authorizedClientService;

  public OAuthController(OAuth2AuthorizedClientService authorizedClientService) {
    this.authorizedClientService = authorizedClientService;
  }

  @GetMapping("/user")
  public Map<String, Object> getUserInfo(OAuth2AuthenticationToken authentication) {
    OAuth2AuthorizedClient client = authorizedClientService.loadAuthorizedClient(
        authentication.getAuthorizedClientRegistrationId(),
        authentication.getName()
    );

    return Map.of(
        "user", authentication.getPrincipal().getAttributes(),
        "accessToken", client.getAccessToken().getTokenValue()
    );
  }
}

