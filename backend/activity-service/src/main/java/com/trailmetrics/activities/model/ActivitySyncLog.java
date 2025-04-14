package com.trailmetrics.activities.model;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;
import lombok.Data;

@Entity
@Table(name = "activity_sync_log")
@Data
public class ActivitySyncLog {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "user_id")
  private Long userId;

  @Column(name = "sync_timestamp")
  private Instant syncTimestamp;

  @ElementCollection
  @CollectionTable(name = "new_activities", joinColumns = @JoinColumn(name = "sync_log_id"))
  @Column(name = "activity_id")
  private Set<Long> newActivityIds = new HashSet<>();

  @ElementCollection
  @CollectionTable(name = "deleted_activities", joinColumns = @JoinColumn(name = "sync_log_id"))
  @Column(name = "activity_id")
  private Set<Long> deletedActivityIds = new HashSet<>();
}
