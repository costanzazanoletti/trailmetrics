package com.trailmetrics.activities.dto;

import java.util.List;
import lombok.Data;

@Data
public class ActivityStreamDTO {

  private StreamData moving;
  private StreamData latlng;
  private StreamData velocitySmooth;
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

    private List<Object> data; // Supports mixed types
    private String seriesType;
    private int originalSize;
    private String resolution;
  }
}
