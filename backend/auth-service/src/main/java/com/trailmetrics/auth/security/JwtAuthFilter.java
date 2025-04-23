package com.trailmetrics.auth.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Collections;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class JwtAuthFilter extends OncePerRequestFilter {

  @Value("${app.jwt-cookie-name}")
  private String jwtCookieName;
  private final JwtUtils jwtUtils;

  public JwtAuthFilter(JwtUtils jwtUtils) {
    this.jwtUtils = jwtUtils;
  }

  @Override
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
      FilterChain filterChain)
      throws ServletException, IOException {

    String token = extractToken(request);

    if (token != null && jwtUtils.isTokenValid(token)) {
      String userId = jwtUtils.extractUsername(token); // Extract user ID from JWT
      // Extract profile data
      String firstname = jwtUtils.extractFirstname(token);
      String lastname = jwtUtils.extractLastname(token);
      String profile = jwtUtils.extractProfileUrl(token);

      // Create a UserPrincipal object with the profile data
      UserPrincipal principal = new UserPrincipal(userId, firstname, lastname, profile);

      // Create an authentication token
      UsernamePasswordAuthenticationToken authentication =
          new UsernamePasswordAuthenticationToken(principal, null, Collections.emptyList());

      authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

      // Set authentication in security context
      SecurityContextHolder.getContext().setAuthentication(authentication);
    }

    filterChain.doFilter(request, response);
  }

  private String extractToken(HttpServletRequest request) {
    String authHeader = request.getHeader(HttpHeaders.AUTHORIZATION);
    if (authHeader != null && authHeader.startsWith("Bearer ")) {
      return authHeader.substring(7);
    }

    if (request.getCookies() != null) {
      for (Cookie cookie : request.getCookies()) {
        if (jwtCookieName.equals(cookie.getName())) {
          return cookie.getValue();
        }
      }
    }

    return null; // No valid token found
  }
}
