package com.trailmetrics.activities.dto;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserSyncRetryMessage {

  private String userId;
  private Instant scheduledRetryTime;
  private Instant sentTimestamp;
}
