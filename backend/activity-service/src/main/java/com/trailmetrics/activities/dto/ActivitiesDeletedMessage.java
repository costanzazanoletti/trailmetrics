package com.trailmetrics.activities.dto;

import java.time.Instant;
import java.util.Set;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivitiesDeletedMessage {

  private String userId;
  private Instant checkedAt;
  private Set<Long> deletedActivityIds;
}
