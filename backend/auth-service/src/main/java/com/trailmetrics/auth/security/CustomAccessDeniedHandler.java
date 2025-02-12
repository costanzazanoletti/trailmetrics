package com.trailmetrics.auth.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

@Component
public class CustomAccessDeniedHandler implements AccessDeniedHandler {

  @Override
  public void handle(HttpServletRequest request, HttpServletResponse response,
      AccessDeniedException accessDeniedException) throws IOException {
    response.setContentType("application/json");
    response.setStatus(HttpServletResponse.SC_FORBIDDEN);

    Map<String, String> errorDetails = new HashMap<>();
    errorDetails.put("error", "Forbidden");
    errorDetails.put("message", accessDeniedException.getMessage());

    String json = new ObjectMapper().writeValueAsString(errorDetails);
    response.getWriter().write(json);
  }
}
