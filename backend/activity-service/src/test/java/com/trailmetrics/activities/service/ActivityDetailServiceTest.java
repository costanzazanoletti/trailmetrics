package com.trailmetrics.activities.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityStreamDTO;
import com.trailmetrics.activities.exception.TrailmetricsAuthServiceException;
import com.trailmetrics.activities.mapper.ActivityStreamMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.mockito.MockitoAnnotations;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.client.HttpClientErrorException;

@SpringBootTest
@ActiveProfiles("test")
class ActivityDetailServiceTest {

  @Autowired
  private ActivityDetailService activityDetailService;

  @MockitoBean
  private StravaClient stravaClient;

  @MockitoBean
  private ActivityRepository activityRepository;

  @MockitoBean
  private ActivityStreamRepository activityStreamRepository;

  @MockitoBean
  private KafkaProducerService kafkaProducerService;

  @MockitoBean
  private KafkaRetryService kafkaRetryService;

  @MockitoBean
  private UserAuthService userAuthService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldFetchAndSaveActivityStreams() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 123L;
    String userId = "user-456";
    int retryCount = 0;

    Activity mockActivity = new Activity();
    mockActivity.setId(activityId);

    ActivityStreamDTO mockStreamDTO = new ActivityStreamDTO();
    List<ActivityStream> mockStreams = List.of(new ActivityStream());

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);
    when(activityRepository.findById(activityId)).thenReturn(Optional.of(mockActivity));
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenReturn(mockStreamDTO);

    // When
    try (MockedStatic<ActivityStreamMapper> mockedMapper = mockStatic(ActivityStreamMapper.class)) {
      mockedMapper.when(
              () -> ActivityStreamMapper.mapStreamsToEntities(mockActivity, mockStreamDTO))
          .thenReturn(mockStreams);

      // When
      activityDetailService.processActivity(activityId, userId, retryCount);

      // Then
      verify(activityRepository, times(1)).findById(activityId);
      verify(stravaClient, times(1)).fetchActivityStream(accessToken, activityId);
      verify(activityStreamRepository, times(1)).saveAll(mockStreams);

      // Then
      verify(userAuthService, times(1)).fetchAccessTokenFromAuthService(userId);
      verify(activityRepository, times(1)).findById(activityId);
      verify(stravaClient, times(1)).fetchActivityStream(accessToken, activityId);
      verify(activityStreamRepository, times(1)).saveAll(mockStreams);
      verify(kafkaProducerService, times(1)).publishActivityProcessed(activityId);
      verify(kafkaRetryService, never()).scheduleActivityRetry(anyString(), anyLong(), anyInt(),
          any());
    }
  }

  @Test
  void shouldHandleActivityNotFound() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 456L;
    String userId = "user-123";
    int retryCount = 0;

    when(activityRepository.findById(activityId)).thenReturn(Optional.empty());
    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);

    activityDetailService.processActivity(activityId, userId, retryCount);

    verify(activityRepository, times(1)).findById(activityId);
    verify(stravaClient, times(1)).fetchActivityStream(accessToken,
        activityId); // API should be called once
    verify(activityStreamRepository, never()).saveAll(any()); // No save should occur

    verify(kafkaProducerService, never()).publishActivityProcessed(
        activityId); // No kafka publishing
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId), eq(0),
        eq(null)); // Rescheduling
  }

  @Test
  void shouldHandleRateLimitAndRetry() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 789L;
    String userId = "user-987";
    int retryCount = 0;

    HttpHeaders headers = new HttpHeaders();
    headers.add("X-ReadRateLimit-Usage", "110,500"); // Short window exceeded
    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenThrow(
        tooManyRequestsException);

    // When
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(activityStreamRepository, never()).saveAll(any()); // No save should occur
    verify(kafkaProducerService, never()).publishActivityProcessed(
        activityId); // No Kafka publishing
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId), eq(0),
        eq(tooManyRequestsException)); // Publish activity retry
  }

  @Test
  void shouldHandleAuthServiceExceptionAndRetry() {
    // Given
    Long activityId = 101L;
    String userId = "user-111";
    int retryCount = 0;

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenThrow(
        new TrailmetricsAuthServiceException("Failed to retrieve token"));

    // When
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId),
        eq(retryCount), eq(null));
    verify(kafkaProducerService, never()).publishActivityProcessed(activityId);
  }

  @Test
  void shouldHandleGeneralExceptionAndRetry() {
    // Given
    Long activityId = 202L;
    String userId = "user-222";
    int retryCount = 0;
    String accessToken = "mockAccessToken";

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenThrow(
        new RuntimeException("Unexpected error"));

    // When
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId),
        eq(retryCount), eq(null));
    verify(kafkaProducerService, never()).publishActivityProcessed(activityId);
  }
}
