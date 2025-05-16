package com.trailmetrics.activities.dto.kafka;

import java.time.Instant;
import java.util.Set;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class EfficiencyZoneRequestMessage {

  private String userId;
  private Instant requestedAt;
  private Set<String> segmentIds;
}
