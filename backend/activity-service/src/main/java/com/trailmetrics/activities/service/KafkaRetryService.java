package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import java.time.Duration;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;

@Service
@Slf4j
@RequiredArgsConstructor
public class KafkaRetryService {

  private final KafkaTemplate<String, UserSyncRetryMessage> kafkaTemplate;
  private final ThreadPoolTaskScheduler scheduler;

  @Value("${strava.api.rate-limit-sleep-minutes}")
  private Integer rateLimitSleepMinutes;


  @Value("${strava.api.rate-limit-short-window}")
  private Integer rateLimitShortWindow;

  @Value("${strava.api.rate-limit-daily}")
  private Integer rateLimitDaily;

  /**
   * Schedules a full user sync retry when too many activities fail due to rate limits.
   */
  public void scheduleUserSyncRetry(String userId, HttpClientErrorException e) {
    int waitTime = determineWaitTime(e);
    Instant retryTime = Instant.now().plusSeconds(waitTime);

    log.warn("Re-queueing full sync for user {} at {}", userId, retryTime);

    // Schedule a retry for the full user sync
    UserSyncRetryMessage retryMessage = new UserSyncRetryMessage(userId);
    scheduler.schedule(() -> kafkaTemplate.send("user-sync-retry-queue", retryMessage), retryTime);
    log.info("Scheduler call completed");
  }

  private int determineWaitTime(HttpClientErrorException e) {
    try {
      HttpHeaders headers = e.getResponseHeaders();
      if (headers == null || headers.getFirst("X-RateLimit-Usage") == null) {
        log.warn("Rate limit headers missing. Defaulting to {} minutes.", rateLimitSleepMinutes);
        return rateLimitSleepMinutes * 60; // Default to 15 minutes
      }

      String rateLimitUsage = headers.getFirst("X-RateLimit-Usage");
      String[] usage = rateLimitUsage.split(",");

      int shortWindowUsage = Integer.parseInt(usage[0]);
      int dailyUsage = Integer.parseInt(usage[1]);

      log.info("Current API Usage - Short Window: {}, Daily: {}", shortWindowUsage, dailyUsage);

      if (shortWindowUsage >= rateLimitShortWindow) {
        return 15 * 60; // 15 minutes
      }
      if (dailyUsage >= rateLimitDaily) {
        return calculateTimeUntilDailyReset();
      }
    } catch (Exception ex) {
      log.warn("Failed to parse Strava rate limit headers. Defaulting to 15 minutes.", ex);
    }

    return rateLimitSleepMinutes * 60; // Default 15 minutes if headers are missing
  }


  /**
   * Calculates the time until the daily API limit resets (defaults to midnight UTC).
   */
  private int calculateTimeUntilDailyReset() {
    Instant now = Instant.now();
    Instant resetTime = now.plusSeconds(86400).truncatedTo(java.time.temporal.ChronoUnit.DAYS);
    return (int) Duration.between(now, resetTime).toSeconds();
  }

/*
  @PostConstruct
  public void logConfigValues() {
    log.info("Loaded rateLimitSleepMinutes: {}", rateLimitSleepMinutes);
    log.info("Loaded rateLimitShortWindow: {}", rateLimitShortWindow);
    log.info("Loaded rateLimitDaily: {}", rateLimitDaily);
  }

 */
}
