package com.trailmetrics.auth.security;

import com.trailmetrics.auth.service.UserAuthService;
import jakarta.servlet.http.Cookie;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProvider;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProviderBuilder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.registration.InMemoryClientRegistrationRepository;
import org.springframework.security.oauth2.client.web.AuthenticatedPrincipalOAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.client.web.DefaultOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.web.OAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;
import org.springframework.security.web.util.matcher.RequestMatcher;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Slf4j
@Configuration
public class SecurityConfig {


  @Value("${spring.security.oauth2.client.registration.strava.client-id}")
  private String clientId;
  @Value("${spring.security.oauth2.client.registration.strava.client-secret}")
  private String clientSecret;
  @Value("${spring.security.oauth2.client.provider.strava.authorization-uri}")
  private String authorizationUri;
  @Value("${spring.security.oauth2.client.provider.strava.token-uri}")
  private String tokenUri;
  @Value("${spring.security.oauth2.client.provider.strava.user-info-uri}")
  private String userInfoUri;
  @Value("${spring.security.oauth2.client.provider.strava.user-name-attribute}")
  private String userNameAttributeName;
  @Value("${spring.security.oauth2.client.registration.strava.client-name}")
  private String clientName;
  @Value("${spring.security.oauth2.client.registration.strava.redirect-uri}")
  private String redirectUri;
  @Value("${spring.security.oauth2.client.registration.strava.scope}")
  private String scope;
  @Value("${app.frontend-url}")
  private String frontendUrl;
  @Value("${app.jwt-cookie-name}")
  private String jwtCookieName;

  private final JwtUtils jwtUtils;

  private final ApiKeyAuthFilter apiKeyAuthFilter;
  private final JwtAuthFilter jwtAuthFilter;

  private final CustomAuthenticationEntryPoint authenticationEntryPoint;
  private final CustomAccessDeniedHandler accessDeniedHandler;

  private final UserAuthService userAuthService;

  private static final List<String> PROTECTED_ENDPOINTS = List.of(
      "/api/**",      // All API endpoints
      "/internal/**"  // Internal microservice routes
  );

  private static final RequestMatcher PROTECTED_ENDPOINT_MATCHER =
      request -> PROTECTED_ENDPOINTS.stream().anyMatch(path ->
          new AntPathRequestMatcher(path).matches(request)
      );


  public SecurityConfig(JwtUtils jwtUtils, ApiKeyAuthFilter apiKeyAuthFilter,
      JwtAuthFilter jwtAuthFilter,
      CustomAuthenticationEntryPoint authenticationEntryPoint,
      CustomAccessDeniedHandler accessDeniedHandler, UserAuthService userAuthService) {
    this.jwtUtils = jwtUtils;
    this.apiKeyAuthFilter = apiKeyAuthFilter;
    this.jwtAuthFilter = jwtAuthFilter;
    this.authenticationEntryPoint = authenticationEntryPoint;
    this.accessDeniedHandler = accessDeniedHandler;
    this.userAuthService = userAuthService;
  }

  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http,
      ClientRegistrationRepository clientRegistrationRepository,
      OAuth2AuthorizedClientService authorizedClientService) throws Exception {
    http
        .cors(cors -> cors.configurationSource(corsConfigurationSource())) // Enable CORS
        .csrf(csrf -> csrf.disable()) // Disable CSRF
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/health").permitAll() // health check
            .requestMatchers("/", "/oauth2/**", "/login/oauth2/**", "/api/auth/user")
            .permitAll() //Allow public login
            .requestMatchers("/internal/**")
            .permitAll() // Allow API Key authenticated requests without OAuth2
            .requestMatchers(PROTECTED_ENDPOINT_MATCHER)
            .authenticated() // Require authentication for other endpoints
            .anyRequest().permitAll()
        )
        .addFilterBefore(apiKeyAuthFilter,
            UsernamePasswordAuthenticationFilter.class) // Apply API Key filter
        .addFilterBefore(jwtAuthFilter,
            UsernamePasswordAuthenticationFilter.class) // Apply JWT filter
        .sessionManagement(session -> session.disable())
        .exceptionHandling(
            ex -> ex.authenticationEntryPoint(authenticationEntryPoint)
                .accessDeniedHandler(accessDeniedHandler))
        .oauth2Login(oauth2 -> oauth2
            .tokenEndpoint(token -> token
                .accessTokenResponseClient(
                    new StravaOAuth2AccessTokenResponseClient(userAuthService))
            )
            .successHandler(((request, response, authentication) -> {
              try {
                OAuth2AuthenticationToken oauthToken = (OAuth2AuthenticationToken) authentication;
                String userId = authentication.getName(); // This is the Strava user ID
                log.info("OAuth Success: UserId={}", userId);
                // Extract attribute from principal
                Map<String, Object> attributes = oauthToken.getPrincipal().getAttributes();
                String firstname = (String) attributes.get("firstname");
                String lastname = (String) attributes.get("lastname");
                String profile = (String) attributes.get("profile");

                // Generate JWT for frontend authentication
                String jwtToken = jwtUtils.generateToken(userId, firstname, lastname, profile);
                // Send JWT in HTTP-only Cookie
                Cookie jwtCookie = new Cookie(jwtCookieName, jwtToken);
                jwtCookie.setHttpOnly(true);
                jwtCookie.setSecure(true);
                jwtCookie.setPath("/");
                response.addCookie(jwtCookie);

                response.sendRedirect(frontendUrl + "/dashboard");
              } catch (IOException e) {
                log.error("Error generating JWT: {}", e.getMessage(), e);
                response.sendRedirect(frontendUrl + "/login?error=jwt_generation_failed");
              }

            }))

        );

    return http.build();
  }

  @Bean
  public OAuth2AuthorizedClientManager authorizedClientManager(
      ClientRegistrationRepository clientRegistrationRepository,
      OAuth2AuthorizedClientRepository authorizedClientRepository) {
    OAuth2AuthorizedClientProvider authorizedClientProvider = OAuth2AuthorizedClientProviderBuilder.builder()
        .authorizationCode()
        .refreshToken()
        .build();

    DefaultOAuth2AuthorizedClientManager authorizedClientManager = new DefaultOAuth2AuthorizedClientManager(
        clientRegistrationRepository, authorizedClientRepository
    );
    authorizedClientManager.setAuthorizedClientProvider(authorizedClientProvider);

    return authorizedClientManager;
  }

  @Bean
  public OAuth2AuthorizedClientRepository authorizedClientRepository(
      OAuth2AuthorizedClientService authorizedClientService) {
    return new AuthenticatedPrincipalOAuth2AuthorizedClientRepository(authorizedClientService);
  }

  @Bean
  public ClientRegistrationRepository clientRegistrationRepository() {

    ClientRegistration stravaRegistration = ClientRegistration.withRegistrationId("strava")
        .clientId(clientId)
        .clientSecret(clientSecret)
        .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
        .scope(scope)
        .authorizationUri(authorizationUri)
        .tokenUri(tokenUri)
        .redirectUri(redirectUri)
        .userInfoUri(userInfoUri)
        .userNameAttributeName(userNameAttributeName)
        .clientName(clientName)
        .build();

    return new InMemoryClientRegistrationRepository(List.of(stravaRegistration));
  }


  @Bean
  public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration configuration = new CorsConfiguration();
    configuration.setAllowedOrigins(List.of(frontendUrl)); // Allow frontend
    configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    configuration.setAllowedHeaders(List.of("*"));
    configuration.setAllowCredentials(true);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", configuration);
    return source;
  }
}