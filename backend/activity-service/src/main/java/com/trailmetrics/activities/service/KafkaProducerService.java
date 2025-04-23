package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.kafka.ActivitiesDeletedMessage;
import com.trailmetrics.activities.dto.kafka.ActivityProcessedMessage;
import com.trailmetrics.activities.dto.kafka.ActivitySyncMessage;
import java.time.Instant;
import java.util.Set;
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
  private final KafkaTemplate<String, ActivitiesDeletedMessage> kafkaUserActivityChangesTemplate;
  private static final String ACTIVITY_PROCESSED_TOPIC = "activity-stream-queue";
  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";
  private static final String ACTIVITIES_DELETED_TOPIC = "activities-deleted-queue";


  public void publishActivityImport(Long activityId, String userId) {
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, Instant.now());
    kafkaActivitySyncTemplate.send(ACTIVITY_SYNC_TOPIC, String.valueOf(activityId), message);
    log.info("Published activity import to Kafka for activity {} to {}", activityId,
        ACTIVITY_SYNC_TOPIC);
  }


  public void publishActivityProcessed(Long activityId, String userId, Instant startDate,
      byte[] compressedStream) {
    ActivityProcessedMessage message = new ActivityProcessedMessage(activityId, userId, startDate,
        Instant.now(), compressedStream);
    kafkaActivityProcessedTemplate.send(ACTIVITY_PROCESSED_TOPIC, String.valueOf(activityId),
        message);
    log.info("Published activity processed to Kafka for activity {} to {}", activityId,
        ACTIVITY_PROCESSED_TOPIC);
  }

  public void publishActivitiesDeleted(String userId,
      Set<Long> deletedActivityIds) {
    ActivitiesDeletedMessage message = new ActivitiesDeletedMessage(userId, Instant.now(),
        deletedActivityIds);

    kafkaUserActivityChangesTemplate.send(ACTIVITIES_DELETED_TOPIC, String.valueOf(userId),
        message);
    log.info("Published deleted activities to Kafka {} for user {}: {}",
        ACTIVITIES_DELETED_TOPIC,
        userId, deletedActivityIds);
  }
}
