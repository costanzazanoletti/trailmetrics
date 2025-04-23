package com.trailmetrics.activities.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;
import lombok.Data;

@Data
public class ActivityDetailsDTO {

  private Long id;
  private String name;
  private double distance;
  @JsonProperty("moving_time")
  private int movingTime;
  @JsonProperty("total_elevation_gain")
  private double totalElevationGain;
  @JsonProperty("sport_type")
  private String sportType;
  @JsonProperty("start_date")
  private Instant startDate;
  private List<Object> latlng;
  private List<Object> altitude;
}

