package com.trailmetrics.activities.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/auth-service/**").permitAll()  // Allow requests to this endpoint
            .anyRequest().authenticated()  // Secure other endpoints
        )
        .csrf(csrf -> csrf.disable())  // Disable CSRF for simplicity
        .httpBasic(httpBasic -> httpBasic.disable());  // Disable Basic Auth

    return http.build();
  }
}
