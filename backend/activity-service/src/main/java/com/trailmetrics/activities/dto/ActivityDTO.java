package com.trailmetrics.activities.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import lombok.Data;

@Data
public class ActivityDTO {

  private Long id;

  private String name;

  private double distance;

  @JsonProperty("moving_time")
  private int movingTime;

  @JsonProperty("total_elevation_gain")
  private double totalElevationGain;

  @JsonProperty("athlete_id")
  private Long athleteId;

  private String type;

  @JsonProperty("sport_type")
  private String sportType;

  @JsonProperty("start_date")
  private Instant startDate;

  @JsonProperty("map_polyline")
  private String mapPolyline;

  @JsonProperty("average_speed")
  private double averageSpeed;

  @JsonProperty("max_speed")
  private double maxSpeed;

  @JsonProperty("average_cadence")
  private Double averageCadence;

  @JsonProperty("average_temp")
  private Integer averageTemp;

  @JsonProperty("average_watts")
  private Double averageWatts;

  @JsonProperty("weighted_average_watts")
  private Double weightedAverageWatts;

  @JsonProperty("has_heartrate")
  private Boolean hasHeartrate;

  @JsonProperty("status")
  private String status;

}

