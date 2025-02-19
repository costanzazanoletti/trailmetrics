package com.trailmetrics.activities.dto;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivitySyncMessage {

  private String userId;
  private Long activityId;
  private int retryCount;  // Tracks how many times this message was retried
  private Instant timestamp; // When the message was sent
}
