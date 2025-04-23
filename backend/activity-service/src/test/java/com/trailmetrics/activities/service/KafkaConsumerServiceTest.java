package com.trailmetrics.activities.service;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.dto.kafka.ActivityRetryMessage;
import com.trailmetrics.activities.dto.kafka.ActivitySyncMessage;
import com.trailmetrics.activities.dto.kafka.UserSyncRetryMessage;
import java.time.Instant;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.kafka.support.Acknowledgment;

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
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, timestamp);

    // When
    kafkaConsumerService.consumeActivity(message, ack);

    // Then
    verify(activityDetailService, times(1)).processActivity(
        eq(activityId), eq(userId), eq(0));
    verify(ack, times(1)).acknowledge();  // Ensure manual acknowledgment
  }

  @Test
  void shouldProcessActivityRetryMessageSuccessfully() {
    // Given
    String userId = "user-123";
    Long activityId = 789L;
    int retryCount = 1;
    Instant scheduledRetryTime = Instant.now().minusSeconds(5); // Already passed
    ActivityRetryMessage message = new ActivityRetryMessage(userId, activityId, retryCount,
        scheduledRetryTime, "Retry reason", Instant.now());

    // When
    kafkaConsumerService.consumeActivityRetry(message, ack);

    // Then
    verify(activityDetailService, times(1)).processActivity(eq(activityId), eq(userId),
        eq(retryCount));
    verify(ack, times(1)).acknowledge();

  }

  @Test
  void shouldPauseBeforeProcessingIfScheduledRetryTimeNotReached() {
    // Given
    String userId = "user-123";
    Long activityId = 456L;
    Instant scheduledRetryTime = Instant.now().plusSeconds(2); // 2 seconds in the future

    ActivityRetryMessage message = new ActivityRetryMessage(userId, activityId, 1,
        scheduledRetryTime, "Rate limit hit", Instant.now());

    // Mock `Thread.sleep()` to verify execution time
    KafkaConsumerService spyConsumer = spy(kafkaConsumerService);
    doReturn(3000L).when(spyConsumer).getWaitTime(scheduledRetryTime);

    // When
    spyConsumer.consumeActivityRetry(message, ack);

    // Then
    verify(spyConsumer, times(1)).getWaitTime(eq(scheduledRetryTime));
    verify(activityDetailService, times(1)).processActivity(eq(activityId), eq(userId), eq(1));
    verify(ack, times(1)).acknowledge();
  }


  @Test
  void shouldPauseBeforeProcessingUserSyncRetryIfScheduledTimeNotReached() {
    // Given
    String userId = "user-123";
    String accessToken = "mockAccessToken";
    Instant scheduledRetryTime = Instant.now().plusSeconds(2); // 2 seconds in the future

    UserSyncRetryMessage message = new UserSyncRetryMessage(userId, scheduledRetryTime,
        Instant.now());

    // Spy on KafkaConsumerService to mock `getWaitTime()`
    KafkaConsumerService spyConsumer = spy(kafkaConsumerService);
    doReturn(3000L).when(spyConsumer).getWaitTime(scheduledRetryTime);

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);

    // When
    spyConsumer.retryUserSync(message, ack);

    // Then
    verify(spyConsumer, times(1)).getWaitTime(eq(scheduledRetryTime));
    verify(activitySyncService, times(1)).syncUserActivities(eq(userId), anyString());
    verify(ack, times(1)).acknowledge();
  }

}