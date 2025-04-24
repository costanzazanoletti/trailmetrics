package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import lombok.Data;

@Entity
@Table(name = "segments")
@Data
public class Segment {

  @Id
  @Column(name = "segment_id", length = 50)
  private String segmentId;

  @Column(name = "activity_id", nullable = false)
  private Long activityId;

  @Column(name = "user_id")
  private String userId;

  @Column(name = "start_distance")
  private Integer startDistance;

  @Column(name = "end_distance")
  private Integer endDistance;

  @Column(name = "segment_length")
  private Integer segmentLength;

  @Column(name = "avg_gradient")
  private Double avgGradient;

  @Column(name = "avg_cadence")
  private Double avgCadence;

  @Column(name = "movement_type", length = 20)
  private String movementType;

  @Column(name = "type", length = 20)
  private String type;

  @Column(name = "grade_category")
  private Double gradeCategory;

  @Column(name = "start_lat")
  private Double startLat;

  @Column(name = "end_lat")
  private Double endLat;

  @Column(name = "start_lng")
  private Double startLng;

  @Column(name = "end_lng")
  private Double endLng;

  @Column(name = "start_altitude")
  private Integer startAltitude;

  @Column(name = "end_altitude")
  private Integer endAltitude;

  @Column(name = "start_time")
  private Integer startTime;

  @Column(name = "end_time")
  private Integer endTime;

  @Column(name = "start_heartrate")
  private Integer startHeartrate;

  @Column(name = "end_heartrate")
  private Integer endHeartrate;

  @Column(name = "avg_heartrate")
  private Double avgHeartrate;

  @Column(name = "avg_speed")
  private Double avgSpeed;

  @Column(name = "elevation_gain")
  private Integer elevationGain;

  @Column(name = "hr_drift")
  private Double hrDrift;

  @Column(name = "road_type")
  private String roadType;

  @Column(name = "surface_type")
  private String surfaceType;

  @Column(name = "temperature")
  private Double temperature;

  @Column(name = "feels_like")
  private Double feelsLike;

  @Column(name = "humidity")
  private Integer humidity;

  @Column(name = "wind")
  private Double wind;

  @Column(name = "weather_id")
  private Integer weatherId;

  @Column(name = "weather_main")
  private String weatherMain;

  @Column(name = "weather_description")
  private String weatherDescription;

  @Column(name = "efficiency_score")
  private Double efficiencyScore;

  @Column(name = "created_at")
  private Instant createdAt;

  @Column(name = "last_updated")
  private Instant lastUpdated;
}
