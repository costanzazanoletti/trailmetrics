package com.trailmetrics.activities.model;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import lombok.Data;

@Embeddable
@Data
public class SegmentSimilarityId implements Serializable {

  @Column(name = "segment_id", length = 50)
  private String segmentId;

  @Column(name = "similar_segment_id", length = 50)
  private String similarSegmentId;

  
  public SegmentSimilarityId() {
  }

  public SegmentSimilarityId(String segmentId, String similarSegmentId) {
    this.segmentId = segmentId;
    this.similarSegmentId = similarSegmentId;
  }
}
