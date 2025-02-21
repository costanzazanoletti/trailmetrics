package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import com.trailmetrics.activities.dto.ActivityRetryMessage;
import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Answers;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;

class KafkaRetryServiceTest {

  private static final String ACTIVITY_RETRY_TOPIC = "activity-retry-queue";
  private static final String USER_SYNC_RETRY_TOPIC = "user-sync-retry-queue";


  @Mock(answer = Answers.RETURNS_DEEP_STUBS)
  private KafkaTemplate<String, UserSyncRetryMessage> userSyncRetryKafkaTemplate;

  @Mock(answer = Answers.RETURNS_DEEP_STUBS)
  private KafkaTemplate<String, ActivityRetryMessage> activityRetryKafkaTemplate;

  @InjectMocks
  private KafkaRetryService kafkaRetryService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);

    ReflectionTestUtils.setField(kafkaRetryService, "rateLimitSleepMinutes", 15);
    ReflectionTestUtils.setField(kafkaRetryService, "rateLimitShortWindow", 200);
    ReflectionTestUtils.setField(kafkaRetryService, "rateLimitDaily", 2000);
    ReflectionTestUtils.setField(kafkaRetryService, "readRateLimitShortWindow", 100);
    ReflectionTestUtils.setField(kafkaRetryService, "readRateLimitDaily", 1000);

    ReflectionTestUtils.setField(kafkaRetryService, "activityRetryKafkaTemplate",
        activityRetryKafkaTemplate);
    ReflectionTestUtils.setField(kafkaRetryService, "userSyncRetryKafkaTemplate",
        userSyncRetryKafkaTemplate);

  }


  @Test
  void shouldScheduleActivityRetry() {

    // Given
    String userId = "user-123";
    Long activityId = 456L;
    int retryCount = 2;
    HttpHeaders headers = new HttpHeaders();
    headers.add("X-ReadRateLimit-Usage", "110,500"); // Short window exceeded

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    Instant expectedRetryTime = Instant.now().plusSeconds(15 * 60); // 15 min delay

    // When
    kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount,
        tooManyRequestsException);

    // Then
    ArgumentCaptor<ActivityRetryMessage> messageCaptor = ArgumentCaptor.forClass(
        ActivityRetryMessage.class);
    verify(activityRetryKafkaTemplate, times(1)).send(eq(ACTIVITY_RETRY_TOPIC),
        messageCaptor.capture());

    ActivityRetryMessage capturedMessage = messageCaptor.getValue();
    assertEquals(userId, capturedMessage.getUserId());
    assertEquals(activityId, capturedMessage.getActivityId());
    assertEquals(retryCount + 1, capturedMessage.getRetryCount()); // Ensure retry count increments
    assertNotNull(capturedMessage.getScheduledRetryTime());
    long diffSeconds = Math.abs(
        Duration.between(expectedRetryTime, capturedMessage.getScheduledRetryTime()).toSeconds());
    assertTrue(diffSeconds <= 120); // Ensure scheduled retry time is close to expected
  }

  @Test
  void shouldScheduleUserSyncRetryWithShortWindowLimit() {
    // Given
    String userId = "user-123";
    HttpHeaders headers = new HttpHeaders();
    headers.add("X-ReadRateLimit-Usage", "110,500"); // Short window exceeded

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS,
        "Too Many Requests",
        headers,
        null,
        StandardCharsets.UTF_8
    );

    Instant expectedRetryTime = Instant.now().plusSeconds(15 * 60); // 15 min delay

    // When
    kafkaRetryService.scheduleUserSyncRetry(userId, tooManyRequestsException);

    // Then
    ArgumentCaptor<UserSyncRetryMessage> messageCaptor = ArgumentCaptor.forClass(
        UserSyncRetryMessage.class);
    verify(userSyncRetryKafkaTemplate, times(1)).send(eq(USER_SYNC_RETRY_TOPIC),
        messageCaptor.capture());

    UserSyncRetryMessage capturedMessage = messageCaptor.getValue();
    assertEquals(userId, capturedMessage.getUserId());
    assertNotNull(capturedMessage.getScheduledRetryTime());
    long diffSeconds = Math.abs(
        Duration.between(expectedRetryTime, capturedMessage.getScheduledRetryTime()).toSeconds());
    assertTrue(diffSeconds <= 120); // Ensure scheduled retry time is close to expected
  }

  @Test
  void shouldScheduleUserSyncRetryWithDailyLimitExceeded() {
    // Given
    String userId = "user-456";
    HttpHeaders headers = new HttpHeaders();
    headers.add("X-RateLimit-Usage", "50,1000"); // Daily limit exceeded

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    Instant expectedResetTime = Instant.now().plusSeconds(86400).truncatedTo(ChronoUnit.DAYS);

    // When
    kafkaRetryService.scheduleUserSyncRetry(userId, tooManyRequestsException);

    // Then
    ArgumentCaptor<UserSyncRetryMessage> messageCaptor = ArgumentCaptor.forClass(
        UserSyncRetryMessage.class);
    verify(userSyncRetryKafkaTemplate, times(1)).send(eq(USER_SYNC_RETRY_TOPIC),
        messageCaptor.capture());

    UserSyncRetryMessage capturedMessage = messageCaptor.getValue();
    long diffSeconds = Math.abs(
        Duration.between(expectedResetTime, capturedMessage.getScheduledRetryTime()).toSeconds());
    assertTrue(diffSeconds <= 120); // Ensure scheduled retry time is close to expected
  }

  @Test
  void shouldNotExceedMaxRetryCount() {
    // Given
    String userId = "user-789";
    Long activityId = 999L;
    int retryCount = 5; // MAX_RETRY_ATTEMPTS
    HttpHeaders headers = new HttpHeaders();
    headers.add("X-RateLimit-Usage", "100,500"); // Short window exceeded

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    // When
    kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount,
        tooManyRequestsException);

    // Then
    verify(activityRetryKafkaTemplate, times(0)).send(eq(ACTIVITY_RETRY_TOPIC),
        any(ActivityRetryMessage.class)); // Ensure no further retries
  }
}
