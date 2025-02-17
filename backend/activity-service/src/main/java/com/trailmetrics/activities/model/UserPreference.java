package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

@Entity
@Table(name = "user_preferences")
@Data
public class UserPreference {

  @Id
  private Long userId;

  @Column(name = "sync_years")
  private Integer syncYears;

  @Column(name = "time_zone")
  private String timezone;
}

