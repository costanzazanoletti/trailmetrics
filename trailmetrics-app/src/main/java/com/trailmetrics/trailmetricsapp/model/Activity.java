package com.trailmetrics.trailmetricsapp.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "activities")
public class Activity {

  @Id
  private Long id;

  private String name;

  private double distance;

  @JsonProperty("moving_time")
  private int movingTime;

  @JsonProperty("total_elevation_gain")
  private double totalElevationGain;

  @JsonProperty("start_date")
  private LocalDateTime startDate;


  private String type;
  
  @JsonProperty("sport_type")
  private String sportType;


  public Activity() {
  }

  public Activity(Long id, String name, double distance, int movingTime, int elapsedTime,
      double totalElevationGain, LocalDateTime startDate, String type, String sportType) {
    this.id = id;
    this.name = name;
    this.distance = distance;
    this.movingTime = movingTime;
    this.totalElevationGain = totalElevationGain;
    this.startDate = startDate;
    this.type = type;
    this.sportType = sportType;
  }

  public String getSportType() {
    return sportType;
  }

  public void setSportType(String sportType) {
    this.sportType = sportType;
  }

  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public LocalDateTime getStartDate() {
    return startDate;
  }

  public void setStartDate(LocalDateTime startDate) {
    this.startDate = startDate;
  }

  public double getTotalElevationGain() {
    return totalElevationGain;
  }

  public void setTotalElevationGain(double totalElevationGain) {
    this.totalElevationGain = totalElevationGain;
  }

  public int getMovingTime() {
    return movingTime;
  }

  public void setMovingTime(int movingTime) {
    this.movingTime = movingTime;
  }

  public double getDistance() {
    return distance;
  }

  public void setDistance(double distance) {
    this.distance = distance;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }
}
