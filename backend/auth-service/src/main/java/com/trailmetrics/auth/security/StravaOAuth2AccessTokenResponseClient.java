package com.trailmetrics.auth.security;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.oauth2.client.endpoint.OAuth2AccessTokenResponseClient;
import org.springframework.security.oauth2.client.endpoint.OAuth2AuthorizationCodeGrantRequest;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.endpoint.OAuth2AccessTokenResponse;
import org.springframework.security.oauth2.core.endpoint.OAuth2ParameterNames;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

public class StravaOAuth2AccessTokenResponseClient
    implements OAuth2AccessTokenResponseClient<OAuth2AuthorizationCodeGrantRequest> {

  
  private final RestTemplate restTemplate = new RestTemplate();
  private final ObjectMapper objectMapper = new ObjectMapper();

  @Override
  public OAuth2AccessTokenResponse getTokenResponse(
      OAuth2AuthorizationCodeGrantRequest authorizationGrantRequest) {

    String tokenUri = authorizationGrantRequest.getClientRegistration().getProviderDetails()
        .getTokenUri();
    String code = authorizationGrantRequest.getAuthorizationExchange().getAuthorizationResponse()
        .getCode();

    if (code == null || code.isEmpty()) {
      throw new RuntimeException("Missing Authorization Code in Token Request!");
    }

    // Create headers for the request
    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

    // Create form body
    MultiValueMap<String, String> requestBody = new LinkedMultiValueMap<>();
    requestBody.add(OAuth2ParameterNames.CLIENT_ID,
        authorizationGrantRequest.getClientRegistration().getClientId());
    requestBody.add(OAuth2ParameterNames.CLIENT_SECRET,
        authorizationGrantRequest.getClientRegistration().getClientSecret());
    requestBody.add(OAuth2ParameterNames.CODE, code);
    requestBody.add(OAuth2ParameterNames.GRANT_TYPE, "authorization_code");

    // Wrap request body in HttpEntity
    HttpEntity<MultiValueMap<String, String>> requestEntity = new HttpEntity<>(requestBody,
        headers);

    // Make request
    ResponseEntity<String> responseEntity = restTemplate.postForEntity(tokenUri, requestEntity,
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
