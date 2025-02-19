package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.ActivitySyncMessage;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class KafkaProducerService {

  private final KafkaTemplate<String, ActivitySyncMessage> kafkaTemplate;

  /**
   * Publishes an activity for background processing.
   */
  public void publishActivityImport(Long activityId, String userId) {
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, 0, Instant.now());
    log.info("Publishing activity import to Kafka: {}", message);
    kafkaTemplate.send("activity-sync-queue", message);
  }

  /**
   * Publishes a retry message for an activity due to API rate limits.
   */
  public void publishActivityRetry(String userId, Long activityId, int retryCount) {
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, retryCount,
        Instant.now());
    log.warn("Requeuing activity {} for user {} (Retry: {})", activityId, userId, retryCount);
    kafkaTemplate.send("activity-sync-queue", message);
  }
}
