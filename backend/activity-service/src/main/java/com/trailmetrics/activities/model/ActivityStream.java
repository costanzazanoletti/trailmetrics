package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.util.List;
import lombok.Data;

@Entity
@Table(name = "activity_streams")
@Data
class ActivityStream {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne
  @JoinColumn(name = "activity_id", nullable = false)
  private Activity activity;

  @Column(name = "type")
  private String type;

  @ElementCollection
  @Column(name = "data")
  private List<Double> data;

  @Column(name = "series_type")
  private String seriesType;

  @Column(name = "original_size")
  private int originalSize;

  @Column(name = "resolution")
  private String resolution;
}
