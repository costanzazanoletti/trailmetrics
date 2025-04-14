package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.ActivitySyncLog;
import java.time.Instant;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ActivitySyncLogRepository extends JpaRepository<ActivitySyncLog, Long> {

  List<ActivitySyncLog> findBySyncTimestampBetween(Instant from, Instant to);
}
