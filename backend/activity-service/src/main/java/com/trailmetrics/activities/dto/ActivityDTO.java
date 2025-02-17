package com.trailmetrics.activities.dto;

import lombok.Data;
import java.time.Instant;

@Data
public class ActivityDTO {
  private Long id;
  private String name;
  private double distance;
  private int moving_time;
  private double total_elevation_gain;
  private Long athlete_id;
  private String type;
  private String sport_type;
  private Instant start_date;
  private String map_polyline;
  private double average_speed;
  private double max_speed;
  private Double average_cadence;
  private Integer average_temp;
  private Double average_watts;
  private Double weighted_average_watts;
  private Boolean has_heartrate;
}

