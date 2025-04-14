package com.trailmetrics.activities.dto;

import java.time.Instant;
import java.util.Set;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserActivityChangesMessage {

  private Long userId;
  private Instant checkedAt;
  private Set<Long> newActivityIds;
  private Set<Long> deletedActivityIds;
}
