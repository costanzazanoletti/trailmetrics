package com.trailmetrics.activities.security;

import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;


@Configuration
@Slf4j
public class SecurityConfig {

  @Value("${app.frontend-url}")
  private String frontendUrl;


  private final JwtAuthFilter jwtAuthFilter;

  public SecurityConfig(JwtAuthFilter jwtAuthFilter) {
    this.jwtAuthFilter = jwtAuthFilter;
  }

  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        .cors(cors -> cors.configurationSource(corsConfigurationSource())) // Enable CORS
        /*.csrf(csrf -> csrf.csrfTokenRepository(
            CookieCsrfTokenRepository.withHttpOnlyFalse())) // Enable CSRF*/
        .csrf(csrf -> csrf.disable()) // DISABLED FOR POSTMAN TEST
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/health").permitAll()
            .requestMatchers("/auth-service/**").permitAll() // test getPublicKey
            .requestMatchers("/api/activities/**").authenticated() // Require JWT for activity APIs
            .anyRequest().permitAll()
        )
        .addFilterBefore(jwtAuthFilter,
            UsernamePasswordAuthenticationFilter.class); // Apply JWT filter

    return http.build();
  }

  @Bean
  public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration configuration = new CorsConfiguration();
    configuration.setAllowedOrigins(List.of(frontendUrl)); // Allow frontend
    configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    configuration.setAllowedHeaders(List.of("*"));
    configuration.setAllowCredentials(true);

    // Logging of allowed origins
    log.info("Configured CORS allowed origins: {}", frontendUrl);
    System.out.println("Configured CORS allowed origins: " + frontendUrl);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", configuration);
    return source;
  }

}
