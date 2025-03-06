package com.trailmetrics.activities.security.logging;

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

    // Logga tutti gli header
    log.info("[REQUEST] {} {}", httpRequest.getMethod(), httpRequest.getRequestURI());

    Enumeration<String> headerNames = httpRequest.getHeaderNames();
    while (headerNames.hasMoreElements()) {
      String headerName = headerNames.nextElement();
      log.info("Header: {} = {}", headerName, httpRequest.getHeader(headerName));
    }

    // Logga il valore dell'IP effettivo cercando nei vari header
    String clientIp = httpRequest.getHeader("X-Forwarded-For");
    if (clientIp == null || clientIp.isEmpty()) {
      clientIp = httpRequest.getHeader("X-Real-IP");
    }
    if (clientIp == null || clientIp.isEmpty()) {
      clientIp = httpRequest.getRemoteAddr();
    }

    log.info("[CLIENT IP] {}", clientIp);

    chain.doFilter(request, response);
  }
}
