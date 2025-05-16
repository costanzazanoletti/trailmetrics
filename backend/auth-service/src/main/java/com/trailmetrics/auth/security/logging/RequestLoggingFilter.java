package com.trailmetrics.auth.security.logging;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.Enumeration;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class RequestLoggingFilter implements Filter {

  @Override
  public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
      throws IOException, ServletException {
    HttpServletRequest httpRequest = (HttpServletRequest) request;

    // Logs all headers
    log.debug("[REQUEST] {} {}", httpRequest.getMethod(), httpRequest.getRequestURI());

    Enumeration<String> headerNames = httpRequest.getHeaderNames();
    while (headerNames.hasMoreElements()) {
      String headerName = headerNames.nextElement();
      log.debug("Header: {} = {}", headerName, httpRequest.getHeader(headerName));
    }

    // Logs the effective ip address
    String clientIp = httpRequest.getHeader("X-Forwarded-For");
    if (clientIp == null || clientIp.isEmpty()) {
      clientIp = httpRequest.getHeader("X-Real-IP");
    }
    if (clientIp == null || clientIp.isEmpty()) {
      clientIp = httpRequest.getRemoteAddr();
    }

    log.debug("[CLIENT IP] {}", clientIp);

    chain.doFilter(request, response);
  }
}
