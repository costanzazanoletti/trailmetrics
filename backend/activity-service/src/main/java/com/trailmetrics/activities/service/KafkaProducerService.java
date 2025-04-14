package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.ActivityProcessedMessage;
import com.trailmetrics.activities.dto.ActivitySyncMessage;
import com.trailmetrics.activities.dto.UserActivityChangesMessage;
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
  private final KafkaTemplate<String, UserActivityChangesMessage> kafkaUserActivityChangesTemplate;
  private static final String ACTIVITY_PROCESSED_TOPIC = "activity-stream-queue";
  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";
  private static final String USER_ACTIVITY_CHANGES_TOPIC = "user-activities-changed-queue";


  public void publishActivityImport(Long activityId, String userId) {
    ActivitySyncMessage message = new ActivitySyncMessage(userId, activityId, Instant.now());
    kafkaActivitySyncTemplate.send(ACTIVITY_SYNC_TOPIC, String.valueOf(activityId), message);
    log.info("Published activity import to Kafka for activity {} to {}", activityId,
        ACTIVITY_SYNC_TOPIC);
  }


  public void publishActivityProcessed(Long activityId, Instant startDate,
      byte[] compressedStream) {
    ActivityProcessedMessage message = new ActivityProcessedMessage(activityId, startDate,
        Instant.now(), compressedStream);
    kafkaActivityProcessedTemplate.send(ACTIVITY_PROCESSED_TOPIC, String.valueOf(activityId),
        message);
    log.info("Published activity processed to Kafka for activity {} to {}", activityId,
        ACTIVITY_PROCESSED_TOPIC);
  }

  public void publishUserActivityChanges(Long userId, Set<Long> newActivityIds,
      Set<Long> deletedActivityIds) {
    UserActivityChangesMessage message = new UserActivityChangesMessage(userId, Instant.now(),
        newActivityIds, deletedActivityIds);

    kafkaUserActivityChangesTemplate.send(USER_ACTIVITY_CHANGES_TOPIC, String.valueOf(userId),
        message);
    log.info("Published activity changes to Kafka {} for user {}: new={}, deleted={}",
        USER_ACTIVITY_CHANGES_TOPIC,
        userId, newActivityIds, deletedActivityIds);
  }
}
