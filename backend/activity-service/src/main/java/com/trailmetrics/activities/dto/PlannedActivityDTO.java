package com.trailmetrics.activities.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import lombok.Data;

@Data
public class PlannedActivityDTO {

  private String name;

  private double distance;

  @JsonProperty("planned_duration")
  private int plannedDuration;

  @JsonProperty("total_elevation_gain")
  private double totalElevationGain;

  @JsonProperty("athlete_id")
  private Long athleteId;

  private String type;

  @JsonProperty("sport_type")
  private String sportType;

  @JsonProperty("start_date")
  private Instant startDate;


}

