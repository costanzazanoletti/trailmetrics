package com.trailmetrics.auth.controller;


import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("api/auth")
public class OAuthController {

  private final OAuth2AuthorizedClientService authorizedClientService;


  public OAuthController(OAuth2AuthorizedClientService authorizedClientService) {
    this.authorizedClientService = authorizedClientService;

  }


  @GetMapping("/user")
  public Map<String, Object> getUser(OAuth2AuthenticationToken authentication) {
    Map<String, Object> response = new HashMap<>();

    if (authentication == null) {
      response.put("authenticated", false);
      return response;
    }

    // Extract user attributes from Strava
    Map<String, Object> attributes = authentication.getPrincipal().getAttributes();

    response.put("authenticated", true);
    response.put("userId", attributes.get("id"));
    response.put("firstname", attributes.get("firstname"));
    response.put("lastname", attributes.get("lastname"));
    response.put("profile", attributes.get("profile"));

    return response;
  }

  @PostMapping("/logout")
  public Map<String, String> logout(HttpServletRequest request, HttpServletResponse response) {
    // Invalidate session
    request.getSession().invalidate();

    // Clear Spring Security authentication
    SecurityContextHolder.clearContext();

    // Remove authentication cookie (JSESSIONID)
    response.setHeader("Set-Cookie", "JSESSIONID=; Path=/; HttpOnly; Max-Age=0; SameSite=None");

    Map<String, String> responseBody = new HashMap<>();
    responseBody.put("message", "Logged out successfully");
    return responseBody;
  }

}

