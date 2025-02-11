package com.trailmetrics.auth.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class ApiKeyAuthFilter extends OncePerRequestFilter {

  @Value("${auth-service.api-key}")
  private String expectedApiKey;

  @Override
  protected void doFilterInternal(HttpServletRequest request,
      HttpServletResponse response,
      FilterChain filterChain) throws ServletException, IOException {
    String apiKey = request.getHeader("X-API-KEY");

    if (request.getRequestURI().startsWith("/internal/")) {
      if (apiKey == null || !apiKey.equals(expectedApiKey)) {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.getWriter().write("Unauthorized: API key required");
        return;
      }
    }

    filterChain.doFilter(request, response);
  }
}
