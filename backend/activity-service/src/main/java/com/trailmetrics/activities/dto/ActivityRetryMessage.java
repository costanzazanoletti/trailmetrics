package com.trailmetrics.activities.dto;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivityRetryMessage {
  private String userId;
  private Long activityId;
  private int retryCount;
  private Instant scheduledRetryTime;
  private String errorReason;
  private Instant sentTimestamp;
}
