package com.trailmetrics.trailmetricsapp.config;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.HashMap;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.security.oauth2.client.endpoint.OAuth2AccessTokenResponseClient;
import org.springframework.security.oauth2.client.endpoint.OAuth2AuthorizationCodeGrantRequest;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.endpoint.OAuth2AccessTokenResponse;
import org.springframework.security.oauth2.core.endpoint.OAuth2ParameterNames;
import org.springframework.web.client.RestTemplate;

public class StravaOAuth2AccessTokenResponseClient implements
    OAuth2AccessTokenResponseClient<OAuth2AuthorizationCodeGrantRequest> {

  private final RestTemplate restTemplate = new RestTemplate();
  private final ObjectMapper objectMapper = new ObjectMapper();

  @Override
  public OAuth2AccessTokenResponse getTokenResponse(
      OAuth2AuthorizationCodeGrantRequest authorizationGrantRequest) {

    String tokenUri = authorizationGrantRequest.getClientRegistration().getProviderDetails()
        .getTokenUri();

    Map<String, String> parameters = new HashMap<>();
    parameters.put(OAuth2ParameterNames.CLIENT_ID,
        authorizationGrantRequest.getClientRegistration().getClientId());
    parameters.put(OAuth2ParameterNames.CLIENT_SECRET,
        authorizationGrantRequest.getClientRegistration().getClientSecret());
    parameters.put(OAuth2ParameterNames.CODE,
        authorizationGrantRequest.getAuthorizationExchange().getAuthorizationResponse().getCode());
    parameters.put(OAuth2ParameterNames.REDIRECT_URI,
        authorizationGrantRequest.getClientRegistration().getRedirectUri());
    parameters.put(OAuth2ParameterNames.GRANT_TYPE,
        authorizationGrantRequest.getGrantType().getValue());

    ResponseEntity<String> responseEntity = restTemplate.postForEntity(tokenUri, parameters,
        String.class);

    try {
      JsonNode jsonNode = objectMapper.readTree(responseEntity.getBody());

      OAuth2AccessToken.TokenType tokenType = OAuth2AccessToken.TokenType.BEARER;
      String accessToken = jsonNode.get("access_token").asText();
      long expiresIn = jsonNode.get("expires_in").asLong();
      String refreshToken = jsonNode.get("refresh_token").asText();

      return OAuth2AccessTokenResponse.withToken(accessToken)
          .tokenType(tokenType)
          .expiresIn(expiresIn)
          .refreshToken(refreshToken)
          .build();

    } catch (Exception e) {
      throw new RuntimeException("Failed to parse Strava OAuth2 access token response", e);
    }
  }
}
