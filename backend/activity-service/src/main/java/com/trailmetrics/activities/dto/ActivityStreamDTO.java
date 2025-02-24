package com.trailmetrics.activities.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import lombok.Data;

@Data
public class ActivityStreamDTO {

  private StreamData moving;
  private StreamData latlng;

  @JsonProperty("velocity_smooth")
  private StreamData velocitySmooth;

  @JsonProperty("grade_smooth")
  private StreamData gradeSmooth;
  private StreamData cadence;
  private StreamData heartrate;
  private StreamData watts;
  private StreamData altitude;
  private StreamData distance;
  private StreamData time;
  private StreamData temp;

  @Data
  public static class StreamData {

    @JsonProperty("data")
    private List<Object> data; // Supports mixed types

    @JsonProperty("series_type")
    private String seriesType;

    @JsonProperty("original_size")
    private int originalSize;

    @JsonProperty("resolution")
    private String resolution;
  }
}
