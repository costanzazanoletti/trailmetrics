package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.ActivityRetryMessage;
import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import java.time.Duration;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;

@Service
@Slf4j
@RequiredArgsConstructor
public class KafkaRetryService {


  private static final String ACTIVITY_RETRY_TOPIC = "activity-retry-queue";
  private static final String USER_SYNC_RETRY_TOPIC = "user-sync-retry-queue";


  private final KafkaTemplate<String, UserSyncRetryMessage> userSyncRetryKafkaTemplate;
  private final KafkaTemplate<String, ActivityRetryMessage> activityRetryKafkaTemplate;


  @Value("${strava.api.rate-limit-sleep-minutes}")
  private Integer rateLimitSleepMinutes;


  @Value("${strava.api.rate-limit-short-window}")
  private Integer rateLimitShortWindow;

  @Value("${strava.api.rate-limit-daily}")
  private Integer rateLimitDaily;

  @Value("${strava.api.read-rate-limit-short-window}")
  private Integer readRateLimitShortWindow;

  @Value("${strava.api.read-rate-limit-daily}")
  private Integer readRateLimitDaily;


  private static final int MAX_RETRY_ATTEMPTS = 5;

  /**
   * Schedules a retry for a specific activity due to rate limit errors.
   */
  public void scheduleActivityRetry(String userId, Long activityId, int retryCount,
      HttpClientErrorException e) {
    if (retryCount >= MAX_RETRY_ATTEMPTS) {
      log.error("Max retry attempts reached for activity {}. Skipping further retries.",
          activityId);
      return;
    }
    int waitTime = determineWaitTime(e);
    Instant scheduledRetryTime = Instant.now().plusSeconds(waitTime);

    log.warn("Re-queueing activity ID {} at {}", activityId, scheduledRetryTime);

    // Create retry message with scheduled execution time
    ActivityRetryMessage retryMessage = new ActivityRetryMessage(
        userId,
        activityId,
        retryCount + 1,
        scheduledRetryTime,
        e.getMessage(),
        Instant.now()
    );

    // Send the message to Kafka immediately (KafkaConsumerService will respect the scheduledRetryTime)
    activityRetryKafkaTemplate.send(ACTIVITY_RETRY_TOPIC, retryMessage);

    log.info("Retry for activity ID {} scheduled at {}", activityId, scheduledRetryTime);
  }

  /**
   * Schedules a full user sync retry when too many activities fail due to rate limits.
   */
  public void scheduleUserSyncRetry(String userId, HttpClientErrorException e) {
    int waitTime = determineWaitTime(e);
    Instant retryTime = Instant.now().plusSeconds(waitTime);

    log.warn("Re-queueing full sync for user {} at {}", userId, retryTime);

    // Schedule a retry for the full user sync
    UserSyncRetryMessage retryMessage = new UserSyncRetryMessage(userId, retryTime, Instant.now());

    // Send the message to Kafka immediately (KafkaConsumerService will respect the scheduledRetryTime)
    userSyncRetryKafkaTemplate.send(USER_SYNC_RETRY_TOPIC, retryMessage);

    log.info("Full sync retry for user {} scheduled at {}", userId, retryTime);
  }

  /**
   * Determines how long to wait before retrying based on API rate limits.
   */
  private int determineWaitTime(HttpClientErrorException e) {

    int shortWindowUsage = extractRateLimitUsage(e, 0);
    int dailyUsage = extractRateLimitUsage(e, 1);

    log.info("Current API Usage - Short={}, Daily={}", shortWindowUsage, dailyUsage);

    // Determine the most restrictive limit (smallest available)
    int effectiveShortWindowLimit = Math.min(rateLimitShortWindow, readRateLimitShortWindow);
    int effectiveDailyLimit = Math.min(rateLimitDaily, readRateLimitDaily);

    // Apply wait times based on exceeded limits
    if (dailyUsage >= effectiveDailyLimit) {
      return calculateTimeUntilDailyReset();
    }
    if (shortWindowUsage >= effectiveShortWindowLimit) {
      return rateLimitSleepMinutes * 60;
    }
    return 0;
  }

  private int calculateTimeUntilDailyReset() {
    Instant now = Instant.now();
    Instant resetTime = now.plusSeconds(86400).truncatedTo(java.time.temporal.ChronoUnit.DAYS);
    return (int) Duration.between(now, resetTime).toSeconds();
  }


  /**
   * Extracts rate limit usage from headers.
   */
  private int extractRateLimitUsage(HttpClientErrorException e, int index) {
    try {
      HttpHeaders headers = e.getResponseHeaders();
      if (headers == null) {
        log.warn("Rate limit headers missing. Assuming max usage to avoid excessive retries.");
        return (index == 0) ? rateLimitShortWindow : rateLimitDaily; // Conservative fallback
      }

      // Get both general and read rate limit values
      String generalUsage = headers.getFirst("X-RateLimit-Usage");
      String readUsage = headers.getFirst("X-ReadRateLimit-Usage");

      Integer generalValue = null, readValue = null;

      if (generalUsage != null) {
        try {
          generalValue = Integer.parseInt(generalUsage.split(",")[index]);
        } catch (NumberFormatException ex) {
          log.warn("Invalid X-RateLimit-Usage format, ignoring: {}", generalUsage);
        }
      }

      if (readUsage != null) {
        try {
          readValue = Integer.parseInt(readUsage.split(",")[index]);
        } catch (NumberFormatException ex) {
          log.warn("Invalid X-ReadRateLimit-Usage format, ignoring: {}", readUsage);
        }
      }

      // Choose the lowest available value, ensuring that at least one value is used
      if (generalValue != null && readValue != null) {
        return Math.min(generalValue, readValue);
      } else if (generalValue != null) {
        return generalValue;
      } else if (readValue != null) {
        return readValue;
      } else {
        log.warn(
            "Both X-RateLimit-Usage and X-ReadRateLimit-Usage are missing or invalid. Assuming max usage.");
        return (index == 0) ? rateLimitShortWindow : rateLimitDaily; // Conservative fallback
      }

    } catch (Exception ex) {
      log.error("Failed to parse rate limit headers. Assuming max usage.", ex);
      return (index == 0) ? rateLimitShortWindow : rateLimitDaily; // Conservative fallback
    }
  }


}
