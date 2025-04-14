package com.trailmetrics.activities.job;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.model.ActivitySyncLog;
import com.trailmetrics.activities.repository.ActivitySyncLogRepository;
import com.trailmetrics.activities.service.KafkaProducerService;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ActivityChangeNotificationServiceTest {

  @InjectMocks
  private ActivityChangeNotificationService activityChangeNotificationService;

  @Mock
  private ActivitySyncLogRepository activitySyncLogRepository;

  @Mock
  private KafkaProducerService kafkaProducerService;

  @Test
  void shouldProcessDailyActivityChangesAndPublishEvents() {
    // Set up test data
    Instant now = Instant.now();
    Instant yesterdayStart = now.minus(1, ChronoUnit.DAYS).truncatedTo(ChronoUnit.DAYS);
    Instant yesterdayEnd = yesterdayStart.plus(1, ChronoUnit.DAYS).minus(1, ChronoUnit.MILLIS);

    ActivitySyncLog log1 = new ActivitySyncLog();
    log1.setUserId(100L);
    log1.setSyncTimestamp(yesterdayStart.plus(Duration.ofHours(12)));
    log1.getNewActivityIds().addAll(Set.of(1L, 2L));

    ActivitySyncLog log2 = new ActivitySyncLog();
    log2.setUserId(200L);
    log2.setSyncTimestamp(yesterdayStart.plus(Duration.ofHours(15)));
    log2.getDeletedActivityIds().add(3L);

    ActivitySyncLog log3 = new ActivitySyncLog();
    log3.setUserId(100L);
    log3.setSyncTimestamp(yesterdayStart.plus(Duration.ofHours(18)));
    log3.getDeletedActivityIds().addAll(Set.of(4L, 5L));

    List<ActivitySyncLog> mockLogs = Arrays.asList(log1, log2, log3);
    when(activitySyncLogRepository.findBySyncTimestampBetween(yesterdayStart, yesterdayEnd))
        .thenReturn(mockLogs);

    // Execute the scheduled job method
    activityChangeNotificationService.processDailyActivityChanges();

    // Verify the interactions
    verify(activitySyncLogRepository, times(1))
        .findBySyncTimestampBetween(yesterdayStart, yesterdayEnd);

    // Verify Kafka calls for user 100 (new activities: 1, 2; deleted activities: 4, 5)
    verify(kafkaProducerService, times(1))
        .publishUserActivityChanges(eq(100L), eq(Set.of(1L, 2L)), eq(Set.of(4L, 5L)));

    // Verify Kafka calls for user 200 (deleted activities: 3)
    verify(kafkaProducerService, times(1))
        .publishUserActivityChanges(eq(200L), eq(Set.of()), eq(Set.of(3L)));
  }

  @Test
  void shouldNotPublishEventsWhenNoChangesFound() {
    // Set up test data with no logs for yesterday
    Instant now = Instant.now();
    Instant yesterdayStart = now.minus(1, ChronoUnit.DAYS).truncatedTo(ChronoUnit.DAYS);
    Instant yesterdayEnd = yesterdayStart.plus(1, ChronoUnit.DAYS).minus(1, ChronoUnit.MILLIS);

    when(activitySyncLogRepository.findBySyncTimestampBetween(yesterdayStart, yesterdayEnd))
        .thenReturn(List.of());

    // Execute the scheduled job method
    activityChangeNotificationService.processDailyActivityChanges();

    // Verify that the Kafka producer was never called
    verify(kafkaProducerService, never()).publishUserActivityChanges(anyLong(), any(), any());
  }

  @Test
  void shouldHandleLogsWithOnlyNewActivities() {
    // Set up test data
    Instant now = Instant.now();
    Instant yesterdayStart = now.minus(1, ChronoUnit.DAYS).truncatedTo(ChronoUnit.DAYS);
    Instant yesterdayEnd = yesterdayStart.plus(1, ChronoUnit.DAYS).minus(1, ChronoUnit.MILLIS);

    ActivitySyncLog log = new ActivitySyncLog();
    log.setUserId(300L);
    log.setSyncTimestamp(yesterdayStart.plus(Duration.ofHours(10)));
    log.getNewActivityIds().addAll(Set.of(6L, 7L, 8L));

    when(activitySyncLogRepository.findBySyncTimestampBetween(yesterdayStart, yesterdayEnd))
        .thenReturn(List.of(log));

    // Execute the scheduled job method
    activityChangeNotificationService.processDailyActivityChanges();

    // Verify Kafka call for user 300
    verify(kafkaProducerService, times(1))
        .publishUserActivityChanges(eq(300L), eq(Set.of(6L, 7L, 8L)), eq(Set.of()));
  }

  @Test
  void shouldHandleLogsWithOnlyDeletedActivities() {
    // Set up test data
    Instant now = Instant.now();
    Instant yesterdayStart = now.minus(1, ChronoUnit.DAYS).truncatedTo(ChronoUnit.DAYS);
    Instant yesterdayEnd = yesterdayStart.plus(1, ChronoUnit.DAYS).minus(1, ChronoUnit.MILLIS);

    ActivitySyncLog log = new ActivitySyncLog();
    log.setUserId(400L);
    log.setSyncTimestamp(yesterdayStart.plus(Duration.ofHours(20)));
    log.getDeletedActivityIds().addAll(Set.of(9L, 10L));

    when(activitySyncLogRepository.findBySyncTimestampBetween(yesterdayStart, yesterdayEnd))
        .thenReturn(List.of(log));

    // Execute the scheduled job method
    activityChangeNotificationService.processDailyActivityChanges();

    // Verify Kafka call for user 400
    verify(kafkaProducerService, times(1))
        .publishUserActivityChanges(eq(400L), eq(Set.of()), eq(Set.of(9L, 10L)));
  }
}


