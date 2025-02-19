package com.trailmetrics.activities.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.ScheduledFuture;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockitoAnnotations;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.client.HttpClientErrorException;

@SpringBootTest
@ActiveProfiles("test")
class KafkaRetryServiceTest {

  @Autowired
  private KafkaRetryService kafkaRetryService;

  @MockitoBean
  private KafkaTemplate<String, UserSyncRetryMessage> kafkaTemplate;

  @MockitoBean
  private ScheduledFuture<?> scheduledFuture; // Mock scheduled future task

  @MockitoBean
  private ThreadPoolTaskScheduler scheduler; // Mock scheduler


  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);

    // Ensure scheduler runs tasks immediately
    doAnswer(invocation -> {
      Runnable task = invocation.getArgument(0);
      task.run();  // Execute immediately
      return scheduledFuture;
    }).when(scheduler).schedule(any(Runnable.class), any(Instant.class));
  }

  @Test
  void shouldScheduleUserSyncRetryWithShortWindowLimit() {
    // Given
    String userId = "user-123";
    HttpHeaders headers = new HttpHeaders();
    headers.add("X-RateLimit-Usage", "100,500"); // Short window exceeded

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    Instant expectedTime = Instant.now().plusSeconds(15 * 60); // 15 min delay

    // When
    kafkaRetryService.scheduleUserSyncRetry(userId, tooManyRequestsException);

    // Then
    verify(scheduler, times(1)).schedule(any(Runnable.class), argThat((Instant actualTime) -> {
          Long diffSeconds = Math.abs(Duration.between(expectedTime, actualTime).toSeconds());
          return diffSeconds <= 120;
        }
    ));
    verify(kafkaTemplate, times(1)).send(eq("user-sync-retry-queue"),
        any(UserSyncRetryMessage.class));
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
    verify(scheduler, times(1)).schedule(any(Runnable.class), argThat((Instant actualTime) -> {
          Long diffSeconds = Math.abs(Duration.between(expectedResetTime, actualTime).toSeconds());
          return diffSeconds <= 120;
        }
    ));
    verify(kafkaTemplate, times(1)).send(eq("user-sync-retry-queue"),
        any(UserSyncRetryMessage.class));
  }


  @Test
  void shouldDefaultTo15MinutesIfRateLimitHeadersAreMissing() {
    // Given
    String userId = "user-789";

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", null, null, StandardCharsets.UTF_8
    );

    Instant expectedTime = Instant.now().plusSeconds(15 * 60); // 15 min delay

    // When
    kafkaRetryService.scheduleUserSyncRetry(userId, tooManyRequestsException);

    // Then
    verify(scheduler, times(1)).schedule(any(Runnable.class), argThat((Instant actualTime) -> {
          Long diffSeconds = Math.abs(Duration.between(expectedTime, actualTime).toSeconds());
          return diffSeconds <= 120;
        }
    ));

    verify(kafkaTemplate, times(1)).send(eq("user-sync-retry-queue"),
        any(UserSyncRetryMessage.class));
  }


}
