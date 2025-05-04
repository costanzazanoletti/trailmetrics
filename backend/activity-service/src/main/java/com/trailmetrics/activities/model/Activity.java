package com.trailmetrics.activities.model;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import jakarta.persistence.Transient;
import java.time.Instant;
import java.util.List;
import lombok.Data;

@Entity
@Table(name = "activities")
@Data
public class Activity {

  @Id
  private Long id;

  @Column(name = "name")
  private String name;

  @Column(name = "distance")
  private double distance;

  @Column(name = "moving_time")
  private int movingTime;

  @Column(name = "total_elevation_gain")
  private double totalElevationGain;

  @Column(name = "athlete_id")
  private Long athleteId;

  @Column(name = "type")
  private String type;

  @Column(name = "sport_type")
  private String sportType;

  @Column(name = "start_date")
  private Instant startDate;

  @Column(name = "description", columnDefinition = "TEXT")
  private String description;

  @Column(name = "map_polyline", columnDefinition = "TEXT")
  private String mapPolyline;

  @Column(name = "average_speed")
  private double averageSpeed;

  @Column(name = "max_speed")
  private double maxSpeed;

  @Column(name = "average_cadence")
  private Double averageCadence;

  @Column(name = "average_temp")
  private Integer averageTemp;

  @Column(name = "average_watts")
  private Double averageWatts;

  @Column(name = "weighted_average_watts")
  private Double weightedAverageWatts;

  @Column(name = "has_heartrate")
  private Boolean hasHeartrate;

  @OneToMany(mappedBy = "activity", cascade = CascadeType.ALL, orphanRemoval = true)
  private List<ActivityStream> streams;

  @OneToOne
  @JoinColumn(name = "id")
  private ActivityStatusTracker statusTracker;

  @Transient
  private ActivityStatus status;

}

