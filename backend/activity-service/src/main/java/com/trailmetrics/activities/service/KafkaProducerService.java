package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.ActivityProcessedMessage;
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

  private final KafkaTemplate<String, ActivitySyncMessage> kafkaActivitySyncTemplate;
  private final KafkaTemplate<String, ActivityProcessedMessage> kafkaActivityProcessedTemplate;
  private static final String ACTIVITY_PROCESSED_TOPIC = "activity-processed-queue";
  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";

  /**
   * Publishes an activity for background processing.
   */
  public void publishActivityImport(Long activityId, String userId) {
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, Instant.now());
    log.info("Publishing activity import to Kafka: {}", message);
    kafkaActivitySyncTemplate.send(ACTIVITY_SYNC_TOPIC, String.valueOf(activityId), message);
  }


  public void publishActivityProcessed(Long activityId) {
    ActivityProcessedMessage message = new ActivityProcessedMessage(activityId,
        Instant.now());
    kafkaActivityProcessedTemplate.send(ACTIVITY_PROCESSED_TOPIC, String.valueOf(activityId),
        message);
    log.info("Sent ActivityProcessedMessage for activity {} to {}", activityId,
        ACTIVITY_PROCESSED_TOPIC);
  }

}
