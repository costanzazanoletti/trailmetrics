package com.trailmetrics.activities.dto.kafka;

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
  private Instant timestamp; // When the message was sent
}
