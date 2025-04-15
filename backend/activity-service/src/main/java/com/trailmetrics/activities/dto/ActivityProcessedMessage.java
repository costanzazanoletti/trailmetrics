package com.trailmetrics.activities.dto;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivityProcessedMessage {

  private Long activityId;
  private String userId;
  private Instant startDate;
  private Instant processedAt;
  private byte[] compressedStream;
}
