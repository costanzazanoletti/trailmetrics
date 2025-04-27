package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import java.time.Instant;
import lombok.Data;

@Entity
@Table(name = "segment_similarity")
@Data
public class SegmentSimilarity {

  @EmbeddedId
  private SegmentSimilarityId id;

  @Column(name = "similarity_score", nullable = false)
  private float similarityScore;

  @Column(name = "rank", nullable = false)
  private int rank;

  @Column(name = "calculated_at")
  private Instant calculatedAt = Instant.now();
}
