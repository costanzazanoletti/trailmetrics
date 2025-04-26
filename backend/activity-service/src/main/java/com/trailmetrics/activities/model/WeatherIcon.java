package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;

@Entity
@Table(name = "weather_icons")
@Data
public class WeatherIcon {

  @Id
  @Column(name = "weather_id")
  Integer weatherId;
  @Column(name = "description")
  String description;
  @Column(name = "icon")
  String icon;
}
