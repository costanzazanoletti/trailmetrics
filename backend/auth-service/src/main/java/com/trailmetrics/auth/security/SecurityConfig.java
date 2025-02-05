package com.trailmetrics.auth.security;

import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProvider;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientProviderBuilder;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.registration.InMemoryClientRegistrationRepository;
import org.springframework.security.oauth2.client.web.AuthenticatedPrincipalOAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.client.web.DefaultOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.web.OAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

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


  @Bean
  public SecurityFilterChain securityFilterChain(HttpSecurity http,
      ClientRegistrationRepository clientRegistrationRepository) throws Exception {
    http
        .cors(cors -> {
        }) // Enable CORS
        .csrf(csrf -> csrf.ignoringRequestMatchers("/api/**",
            "/kafka/**")) // Disable CSRF only for API
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/", "/oauth2/**", "/login/oauth2/**").permitAll() //Allow public login
            .anyRequest().authenticated()
        )
        .oauth2Login(oauth2 -> oauth2
            .tokenEndpoint(token -> token
                .accessTokenResponseClient(new StravaOAuth2AccessTokenResponseClient())
            )
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
    configuration.setAllowedOrigins(
        List.of("http://localhost:5173")); // Allow requests from React frontend
    configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    configuration.setAllowedHeaders(List.of("*"));
    configuration.setAllowCredentials(true);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", configuration);
    return source;
  }
}