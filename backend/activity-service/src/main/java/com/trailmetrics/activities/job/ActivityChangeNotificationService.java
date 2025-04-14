package com.trailmetrics.activities.job;

import com.trailmetrics.activities.model.ActivitySyncLog;
import com.trailmetrics.activities.repository.ActivitySyncLogRepository;
import com.trailmetrics.activities.service.KafkaProducerService;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class ActivityChangeNotificationService {

  private final ActivitySyncLogRepository activitySyncLogRepository;
  private final KafkaProducerService kafkaProducerService;

  @Scheduled(cron = "0 0 0 * * ?") // Runs at midnight every day
  public void processDailyActivityChanges() {
    log.info("Starting daily activity change processing...");

    Instant now = Instant.now();
    Instant yesterdayStart = now.minus(1, ChronoUnit.DAYS).truncatedTo(ChronoUnit.DAYS);
    Instant yesterdayEnd = yesterdayStart.plus(1, ChronoUnit.DAYS)
        .minus(1, ChronoUnit.MILLIS); // End of yesterday

    List<ActivitySyncLog> logs = activitySyncLogRepository.findBySyncTimestampBetween(
        yesterdayStart, yesterdayEnd);

    Map<Long, Set<Long>> newActivitiesByUser = new HashMap<>();
    Map<Long, Set<Long>> deletedActivitiesByUser = new HashMap<>();

    for (ActivitySyncLog log : logs) {
      Long userId = log.getUserId();
      newActivitiesByUser.computeIfAbsent(userId, k -> new HashSet<>())
          .addAll(log.getNewActivityIds());
      deletedActivitiesByUser.computeIfAbsent(userId, k -> new HashSet<>())
          .addAll(log.getDeletedActivityIds());
    }

    Set<Long> allChangedUsers = new HashSet<>(newActivitiesByUser.keySet());
    allChangedUsers.addAll(deletedActivitiesByUser.keySet());

    for (Long userId : allChangedUsers) {
      Set<Long> newIds = newActivitiesByUser.getOrDefault(userId, Set.of());
      Set<Long> deletedIds = deletedActivitiesByUser.getOrDefault(userId, Set.of());
      if (!newIds.isEmpty() || !deletedIds.isEmpty()) {
        log.info("Sending activity changes for user {}: new={}, deleted={}", userId, newIds.size(),
            deletedIds.size());
        kafkaProducerService.publishUserActivityChanges(userId, newIds, deletedIds);
      }
    }

    log.info("Finished daily activity change processing.");
  }
}
