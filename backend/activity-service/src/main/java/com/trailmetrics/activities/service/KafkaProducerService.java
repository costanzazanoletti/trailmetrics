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

  private final KafkaTemplate<String, ActivitySyncMessage> kafkaActivitySyncTemplate;


  /**
   * Publishes an activity for background processing.
   */
  public void publishActivityImport(Long activityId, String userId) {
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, Instant.now());
    log.info("Publishing activity import to Kafka: {}", message);
    kafkaActivitySyncTemplate.send("activity-sync-queue", message);
  }


}
