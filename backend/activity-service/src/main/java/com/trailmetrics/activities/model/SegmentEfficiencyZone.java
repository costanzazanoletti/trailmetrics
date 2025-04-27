package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import lombok.Data;

@Entity
@Table(name = "segment_efficiency_zone")
@Data
public class SegmentEfficiencyZone {

  @Id
  @Column(name = "segment_id", length = 50)
  private String segmentId;

  @Column(name = "zone_among_similars")
  private String zoneAmongSimilars;

  @Column(name = "zone_among_grade_category")
  private String zoneAmongGradeCategory;

  @Column(name = "calculated_at")
  private Instant calculatedAt = Instant.now(); // default now
}
