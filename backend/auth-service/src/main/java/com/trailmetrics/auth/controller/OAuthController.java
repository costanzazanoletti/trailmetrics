package com.trailmetrics.auth.controller;


import com.trailmetrics.auth.security.UserPrincipal;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("api/auth")
public class OAuthController {

  @Value("${app.jwt-cookie-name}")
  private String jwtCookieName;

  private final OAuth2AuthorizedClientService authorizedClientService;


  public OAuthController(OAuth2AuthorizedClientService authorizedClientService) {
    this.authorizedClientService = authorizedClientService;

  }


  @GetMapping("/user")
  public Map<String, Object> getUser(Authentication authentication) {
    Map<String, Object> response = new HashMap<>();

    if (authentication == null || !authentication.isAuthenticated() ||
        authentication.getPrincipal().equals("anonymousUser")) {
      response.put("authenticated", false);
      return response;
    }

    UserPrincipal user = (UserPrincipal) authentication.getPrincipal();

    response.put("authenticated", true);
    response.put("userId", user.userId());
    response.put("firstname", user.firstname());
    response.put("lastname", user.lastname());
    response.put("profileUrl", user.profileUrl());

    return response;
  }

  @PostMapping("/logout")
  public ResponseEntity<Object> logout(HttpServletRequest request, HttpServletResponse response) {
    // Invalidate session
    request.getSession().invalidate();

    // Clear Spring Security authentication
    SecurityContextHolder.clearContext();

    // Remove authentication cookie (JSESSIONID)
    response.setHeader("Set-Cookie", "JSESSIONID=; Path=/; HttpOnly; Max-Age=0; SameSite=None");
    Cookie cookie = new Cookie(jwtCookieName, "");
    cookie.setMaxAge(0);
    cookie.setHttpOnly(true);
    cookie.setPath("/"); // Match path of original cookie
    response.addCookie(cookie);

    return ResponseEntity.ok().build();
  }

}

