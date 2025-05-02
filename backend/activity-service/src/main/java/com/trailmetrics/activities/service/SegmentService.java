package com.trailmetrics.activities.service;

import com.trailmetrics.activities.exception.ResourceNotFoundException;
import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class SegmentService {

  private final SegmentRepository segmentRepository;

  public List<Segment> getTopSimilarSegments(String segmentId) {
    Segment segment = segmentRepository.findById(segmentId)
        .orElseThrow(() -> new ResourceNotFoundException("Segment not found: " + segmentId));
    return segmentRepository.findTopSimilarSegments(segment.getSegmentId());
  }

  public List<Segment> getTopSegmentsByGrade(String segmentId) {
    Segment segment = segmentRepository.findById(segmentId)
        .orElseThrow(() -> new ResourceNotFoundException("Segment not found: " + segmentId));

    Double gradeCategory = segment.getGradeCategory();
    return segmentRepository.findTopByGradeCategory(gradeCategory, segmentId,
        PageRequest.of(0, 5));

  }
}
