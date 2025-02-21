package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.ActivityRetryMessage;
import com.trailmetrics.activities.dto.ActivitySyncMessage;
import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;

@Service
@Slf4j
@RequiredArgsConstructor
public class KafkaConsumerService {

  private final ActivityDetailService activityDetailService;
  private final UserAuthService userAuthService;
  private final KafkaRetryService kafkaRetryService;
  private final ActivitySyncService activitySyncService;

  private static final int MAX_RETRY_ATTEMPTS = 5; // Prevents infinite retry loops
  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";
  private static final String ACTIVITY_RETRY_TOPIC = "activity-retry-queue";
  private static final String USER_SYNC_RETRY_TOPIC = "user-sync-retry-queue";
  private static final String KAFKA_ACTIVITY_GROUP = "activity-group";

  /**
   * Listens for activity imports from `activity-sync-queue`. Processes individual activities.
   */
  @KafkaListener(topics = ACTIVITY_SYNC_TOPIC, groupId = KAFKA_ACTIVITY_GROUP)
  public void consumeActivity(ActivitySyncMessage message, Acknowledgment ack) {
    processActivity(message.getUserId(), message.getActivityId(), 0, ack);
  }

  /**
   * Listens for activity retries from `activity-retry-queue`. Retries failed activities.
   */
  @KafkaListener(topics = ACTIVITY_RETRY_TOPIC, groupId = KAFKA_ACTIVITY_GROUP)
  public void consumeActivityRetry(ActivityRetryMessage message, Acknowledgment ack) {
    // Ensure we only process activities after their scheduled retry time
    if (Instant.now().isBefore(message.getScheduledRetryTime())) {
      log.info("Skipping early execution for activity {}. Scheduled for {}",
          message.getActivityId(), message.getScheduledRetryTime());
      return;
    }

    processActivity(message.getUserId(), message.getActivityId(), message.getRetryCount(), ack);
  }


  /**
   * Listens for user sync retries from `user-sync-retry-queue`. Retries full user sync after rate
   * limit expires.
   */
  @KafkaListener(topics = USER_SYNC_RETRY_TOPIC

      , groupId = KAFKA_ACTIVITY_GROUP)
  public void retryUserSync(UserSyncRetryMessage message, Acknowledgment ack) {
    // Ensure we only process syncs after their scheduled retry time
    if (Instant.now().isBefore(message.getScheduledRetryTime())) {
      log.info("Skipping early execution for user {} sync. Scheduled for {}", message.getUserId(),
          message.getScheduledRetryTime());
      return;
    }
    String userId = message.getUserId();
    try {
      log.info("Retrying full sync for user ID: {}", userId);

      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);
      activitySyncService.syncUserActivities(userId, accessToken);

      ack.acknowledge();
    } catch (HttpClientErrorException.TooManyRequests e) {
      log.warn("Rate limit hit while retrying full user sync for user {}. Will retry later.",
          userId);
      kafkaRetryService.scheduleUserSyncRetry(userId, e);
    } catch (Exception e) {
      log.error("Unexpected error while retrying user sync for user {}", userId, e);
      ack.acknowledge();
    }
  }

  /**
   * Processes an activity by fetching details from Strava.
   */
  private void processActivity(String userId, Long activityId, int retryCount, Acknowledgment ack) {
    try {
      log.info("Processing activity ID {} for user {} (Retry: {})", activityId, userId, retryCount);

      // Fetch user access token
      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

      // Process activity (fetch streams)
      activityDetailService.fetchStreamAndUpdateActivity(accessToken, activityId, userId);

      // Successfully processed, acknowledge the Kafka message
      ack.acknowledge();
      log.info("Successfully processed activity ID: {}", activityId);

    } catch (HttpClientErrorException.TooManyRequests e) {
      log.warn("Rate limit reached for activity ID {}. Retrying (Attempt: {})", activityId,
          retryCount);

      if (retryCount < MAX_RETRY_ATTEMPTS) {
        kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, e);
      } else {
        log.error("Max retry attempts reached for activity ID {}. Skipping processing.",
            activityId);
        ack.acknowledge();
      }

    } catch (Exception e) {
      log.error("Error processing activity ID {}", activityId, e);
      ack.acknowledge(); // Acknowledge to prevent infinite loop on bad messages
    }
  }

}
