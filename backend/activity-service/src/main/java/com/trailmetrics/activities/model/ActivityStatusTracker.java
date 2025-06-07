package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.time.Instant;
import lombok.Data;

@Entity
@Table(name = "activity_status_tracker")
@Data
public class ActivityStatusTracker {

  @Id
  @Column(name = "activity_id")
  private Long activityId;

  @OneToOne(mappedBy = "statusTracker")
  private Activity activity;

  @Column(name = "segment_status")
  private boolean segmentStatus;

  @Column(name = "terrain_status")
  private boolean terrainStatus;

  @Column(name = "weather_status")
  private boolean weatherStatus;

  @Column(name = "not_processable")
  private boolean notProcessable;

  @Column(name = "similarity_processed_at")
  private Instant similarityProcessedAt;

  @Column(name = "prediction_executed_at")
  private Instant predictionExecutedAt;

  @Column(name = "last_updated")
  private Instant lastUpdated;
}
