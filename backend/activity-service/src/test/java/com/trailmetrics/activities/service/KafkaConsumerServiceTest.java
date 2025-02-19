package com.trailmetrics.activities.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.dto.ActivitySyncMessage;
import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.repository.ActivityRepository;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.web.client.HttpClientErrorException;

class KafkaConsumerServiceTest {

  @Mock
  private ActivityDetailService activityDetailService;

  @Mock
  private ActivitySyncService activitySyncService;

  @Mock
  private UserAuthService userAuthService;

  @Mock
  private KafkaRetryService kafkaRetryService;

  @Mock
  private ActivityRepository activityRepository;

  @Mock
  private Acknowledgment ack;  // Mocking manual Kafka acknowledgment

  @InjectMocks
  private KafkaConsumerService kafkaConsumerService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldConsumeActivitySyncMessageSuccessfully() {
// Given
    String userId = "user-123";
    Long activityId = 456L;
    Instant timestamp = Instant.now();
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, 0, timestamp);

    when(activityRepository.findById(activityId)).thenReturn(java.util.Optional.of(new Activity()));
    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn("mockAccessToken");

    // When
    kafkaConsumerService.consumeActivity(message, ack);

    // Then
    verify(activityDetailService, times(1)).processActivity(anyString(), eq(activityId));
    verify(ack, times(1)).acknowledge();  // Ensure manual acknowledgment
  }

  @Test
  void shouldRetryActivitySyncOnRateLimit() {
    // Given
    String userId = "user-123";
    Long activityId = 456L;
    Instant timestamp = Instant.now();

    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, 1, timestamp);

    when(activityRepository.findById(activityId)).thenReturn(java.util.Optional.of(new Activity()));
    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn("mockAccessToken");

    // Simulate a "429 Too Many Requests" error when processing the activity
    doThrow(HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS,
        "Too Many Requests",
        HttpHeaders.EMPTY,
        null,
        StandardCharsets.UTF_8
    )).when(activityDetailService).processActivity(anyString(), eq(activityId));

    // When
    kafkaConsumerService.consumeActivity(message, ack);

    // Then
    verify(kafkaRetryService, times(1)).scheduleUserSyncRetry(eq(userId), any());
    verify(ack, never()).acknowledge();  // Should NOT acknowledge, letting Kafka retry
  }

  @Test
  void shouldConsumeUserSyncRetryMessageSuccessfully() {
    // Given
    String userId = "user-123";
    UserSyncRetryMessage message = new UserSyncRetryMessage(userId);

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn("mockAccessToken");

    // When
    kafkaConsumerService.retryUserSync(message, ack);

    // Then
    verify(activitySyncService, times(1)).syncUserActivities(eq(userId), anyString());
    verify(ack, times(1)).acknowledge();
  }
}