package com.trailmetrics.activities.dto;

import lombok.Data;

@Data
public class SegmentDTO {

  private String segmentId;
  private Long activityId;

  private Integer startDistance;
  private Integer endDistance;
  private Double avgGradient;
  private Double avgCadence;

  private Double startLat;
  private Double endLat;
  private Double startLng;
  private Double endLng;

  private Integer startAltitude;
  private Integer endAltitude;

  private Integer startTime;
  private Integer endTime;

  private Double avgSpeed;
  private Double elevationGain;
  private Double efficiencyScore;

  private Integer startHeartrate;
  private Integer endHeartrate;
  private Double avgHeartrate;

  private String roadType;
  private String surfaceType;

  private Double temperature;
  private Integer humidity;
  private Double wind;
  private Integer weatherId;
  private String weatherMain;
  private String weatherDescription;

}
