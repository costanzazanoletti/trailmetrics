package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.dto.SegmentDTO;
import com.trailmetrics.activities.exception.ResourceNotFoundException;
import com.trailmetrics.activities.mapper.SegmentMapper;
import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.response.ApiResponse;
import com.trailmetrics.activities.response.ApiResponseFactory;
import com.trailmetrics.activities.service.SegmentEfficiencyZoneService;
import com.trailmetrics.activities.service.SegmentService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/segments")
@RequiredArgsConstructor
public class SegmentController {

  private final SegmentService segmentService;
  private final SegmentMapper segmentMapper;
  private final SegmentEfficiencyZoneService segmentEfficiencyZoneService;

  @GetMapping("/{segmentId}/similar")
  public ResponseEntity<ApiResponse<List<SegmentDTO>>> getSimilarSegments(
      @PathVariable String segmentId) {
    try {
      List<Segment> similarSegments = segmentService.getTopSimilarSegments(segmentId);
      // Compute efficiency zones for related activities asynchronously
      similarSegments.forEach(
          segment -> segmentEfficiencyZoneService.recalculateZonesForActivityAsync(
              segment.getActivityId()));

      List<SegmentDTO> segmentDTOs = similarSegments.stream()
          .map(segmentMapper::toDTO)
          .toList();

      return ApiResponseFactory.ok(segmentDTOs, "Fetched similar segments");

    } catch (ResourceNotFoundException e) {
      return ApiResponseFactory.error("Segment not found", HttpStatus.NOT_FOUND);
    } catch (Exception e) {
      return ApiResponseFactory.error("Failed to fetch similar segments",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @GetMapping("/{segmentId}/top-grade")
  public ResponseEntity<ApiResponse<List<SegmentDTO>>> getTopSegmentsByGrade(
      @PathVariable String segmentId) {
    try {
      List<Segment> topSegments = segmentService.getTopSegmentsByGrade(segmentId);
      List<SegmentDTO> topSegmentsDTO = topSegments.stream().map(segmentMapper::toDTO).toList();

      return ApiResponseFactory.ok(topSegmentsDTO, "Fetched same grade category top segments");
    } catch (ResourceNotFoundException e) {
      return ApiResponseFactory.error("Segment not found", HttpStatus.NOT_FOUND);
    } catch (Exception e) {
      return ApiResponseFactory.error("Failed to fetch same grade category top segments",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }

  }

}

