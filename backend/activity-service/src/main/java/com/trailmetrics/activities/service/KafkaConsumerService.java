package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.ActivitySyncMessage;
import com.trailmetrics.activities.dto.UserSyncRetryMessage;
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

  /**
   * Listens for activity imports from `activity-sync-queue`. Processes individual activities by
   * fetching details & streams.
   */
  @KafkaListener(topics = "activity-sync-queue", groupId = "activity-group")
  public void consumeActivity(ActivitySyncMessage message, Acknowledgment ack) {
    String userId = message.getUserId();
    Long activityId = message.getActivityId();
    int retryCount = message.getRetryCount();
    try {

      log.info("Processing activity ID {} for user {} (Retry: {})", activityId, userId, retryCount);

      // Fetch user access token
      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

      // Process activity (fetch streams)
      activityDetailService.processActivity(accessToken, activityId);

      // Successfully processed, acknowledge the Kafka message
      ack.acknowledge();
      log.info("Successfully processed activity ID: {}", activityId);

    } catch (HttpClientErrorException.TooManyRequests e) {
      log.warn("Rate limit reached for activity ID {}. Retrying (Attempt: {})", activityId,
          retryCount);

      if (retryCount < MAX_RETRY_ATTEMPTS) {
        kafkaRetryService.scheduleUserSyncRetry(userId, e);

      } else {
        log.error("Max retry attempts reached for activity ID {}. Skipping processing.",
            activityId);
        ack.acknowledge();
      }

    } catch (Exception e) {
      log.error("Error processing activity ID {}", message, e);
      ack.acknowledge(); // Acknowledge to prevent infinite loop on bad messages
    }
  }

  /**
   * Listens for user sync retries from `user-sync-retry-queue`. Retries full user sync after rate
   * limit expires.
   */
  @KafkaListener(topics = "user-sync-retry-queue", groupId = "activity-group")
  public void retryUserSync(UserSyncRetryMessage message, Acknowledgment ack) {
    String userId = message.getUserId();
    try {
      log.info("Retrying full sync for user ID: {}", userId);

      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);
      activitySyncService.syncUserActivities(userId, accessToken);

      ack.acknowledge();
    } catch (HttpClientErrorException.TooManyRequests e) {
      log.warn("Rate limit hit while retrying full user sync for user {}. Will retry later.",
          userId);
      throw e; // Kafka will handle retrying
    } catch (Exception e) {
      log.error("Unexpected error while retrying user sync for user {}", userId, e);
      ack.acknowledge();
    }
  }
}
