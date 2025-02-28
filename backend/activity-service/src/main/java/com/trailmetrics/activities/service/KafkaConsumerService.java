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
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.HttpClientErrorException;

@Service
@Slf4j
@RequiredArgsConstructor
public class KafkaConsumerService {

  private final ActivityDetailService activityDetailService;
  private final UserAuthService userAuthService;
  private final KafkaRetryService kafkaRetryService;
  private final ActivitySyncService activitySyncService;

  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";
  private static final String ACTIVITY_RETRY_TOPIC = "activity-retry-queue";
  private static final String USER_SYNC_RETRY_TOPIC = "user-sync-retry-queue";
  private static final String KAFKA_ACTIVITY_GROUP = "activity-group";

  /**
   * Listens for activity imports from `activity-sync-queue`. Processes individual activities.
   */
  @Transactional
  @KafkaListener(topics = ACTIVITY_SYNC_TOPIC, groupId = KAFKA_ACTIVITY_GROUP)
  public void consumeActivity(ActivitySyncMessage message, Acknowledgment ack) {
    log.info("Reading message in queue {} for activity ID {}", ACTIVITY_SYNC_TOPIC,
        message.getActivityId());
    activityDetailService.processActivity(message.getActivityId(), message.getUserId(), 0);
    ack.acknowledge();
  }

  /**
   * Listens for activity retries from `activity-retry-queue`. Retries failed activities.
   */
  @Transactional
  @KafkaListener(topics = ACTIVITY_RETRY_TOPIC, groupId = KAFKA_ACTIVITY_GROUP)
  public void consumeActivityRetry(ActivityRetryMessage message, Acknowledgment ack) {
    log.info("Reading message in queue {} for activity ID {}", ACTIVITY_RETRY_TOPIC,
        message.getActivityId());
    // Ensure we only process activities after their scheduled retry time
    if (Instant.now().isBefore(message.getScheduledRetryTime())) {
      log.info("Pausing execution for activity ID {}. Scheduled for {}",
          message.getActivityId(), message.getScheduledRetryTime());
      try {
        Thread.sleep(getWaitTime(message.getScheduledRetryTime()));
      } catch (InterruptedException e) {
        log.warn("Interrupted while waiting for scheduled retry time", e);
      }
    }

    // Process activity
    activityDetailService.processActivity(message.getActivityId(), message.getUserId(),
        message.getRetryCount());
    ack.acknowledge(); // Explicitly acknowledge after processing

  }


  /**
   * Listens for user sync retries from `user-sync-retry-queue`. Retries full user sync after rate
   * limit expires.
   */
  @KafkaListener(topics = USER_SYNC_RETRY_TOPIC, groupId = KAFKA_ACTIVITY_GROUP)
  public void retryUserSync(UserSyncRetryMessage message, Acknowledgment ack) {
    log.info("Reading message in queue {} for user ID {}", USER_SYNC_RETRY_TOPIC,
        message.getUserId());
    // Ensure we only process syncs after their scheduled retry time
    if (Instant.now().isBefore(message.getScheduledRetryTime())) {
      log.info("Pausing execution for user {} sync. Scheduled for {}", message.getUserId(),
          message.getScheduledRetryTime());
      try {
        Thread.sleep(getWaitTime(message.getScheduledRetryTime()));
      } catch (InterruptedException e) {
        log.warn("Interrupted while waiting for scheduled retry time", e);
      }
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

  protected long getWaitTime(Instant scheduledRetryTime) {
    return
        1000 + scheduledRetryTime.toEpochMilli() - Instant.now().toEpochMilli();
  }
}
