package com.trailmetrics.activities.dto.kafka;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivityProcessedMessage {

  private Long activityId;
  private Boolean isPlanned;
  private String userId;
  private Instant startDate;
  private Instant processedAt;
  private byte[] compressedStream;
}
