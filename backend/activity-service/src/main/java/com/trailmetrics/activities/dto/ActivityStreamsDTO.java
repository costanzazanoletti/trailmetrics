package com.trailmetrics.activities.dto;

import java.util.List;
import lombok.Data;

@Data
public class ActivityStreamsDTO {

  private List<List<Double>> latlng;
  private List<Double> altitude;
  private List<Integer> heartrate;
  private List<Double> distance;
  private List<Double> speed;
  private List<Integer> time;
  private List<Double> grade;
  private List<Integer> cadence;
}
