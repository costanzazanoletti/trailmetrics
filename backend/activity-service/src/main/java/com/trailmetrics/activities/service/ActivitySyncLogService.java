package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.ActivitySyncLog;
import com.trailmetrics.activities.repository.ActivitySyncLogRepository;
import java.time.Instant;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class ActivitySyncLogService {

  private final ActivitySyncLogRepository activitySyncLogRepository;

  public void recordSyncLog(Long userId, Set<Long> newActivitiesThisSync,
      Set<Long> activitiesToDelete) {
    // Record the sync log
    ActivitySyncLog syncLog = new ActivitySyncLog();
    syncLog.setUserId(userId);
    syncLog.setSyncTimestamp(Instant.now());
    syncLog.getNewActivityIds().addAll(newActivitiesThisSync);
    syncLog.getDeletedActivityIds().addAll(activitiesToDelete);
  }
}
