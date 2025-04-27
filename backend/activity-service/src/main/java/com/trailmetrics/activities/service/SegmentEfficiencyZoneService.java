package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.model.SegmentEfficiencyZone;
import com.trailmetrics.activities.repository.SegmentEfficiencyZoneRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import jakarta.transaction.Transactional;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class SegmentEfficiencyZoneService {

  private final SegmentEfficiencyZoneRepository zoneRepository;
  private final SegmentRepository segmentRepository;

  @Transactional
  public void recalculateZonesForActivity(Long activityId) {
    List<Segment> segments = segmentRepository.findByActivityId(activityId);

    log.info("Computing segment efficiency zones for activity {}", activityId);

    for (Segment segment : segments) {
      String segmentId = segment.getSegmentId();
      try {
        getOrCalculateZone(segmentId);
      } catch (Exception e) {
        // Log warning
        log.warn("Failed to calculate efficiency zone for segment {}: ", segmentId, e);
      }
    }
  }

  public SegmentEfficiencyZone getOrCalculateZone(String segmentId) {
    // Check if exists
    Optional<SegmentEfficiencyZone> existing = zoneRepository.findBySegmentId(segmentId);

    if (existing.isPresent()) {
      SegmentEfficiencyZone zone = existing.get();

      // Fetch the date of the latest similarity computation
      Optional<Instant> latestSimilarityCalculationOpt = segmentRepository
          .findLatestCalculatedAtBySegmentId(segmentId);
      // if it doesn't exist we cannot proceed
      if (latestSimilarityCalculationOpt.isEmpty()) {
        throw new IllegalStateException(
            "Cannot calculate efficiency zones: no segment similarity data available for segment "
                + segmentId);
      }

      Instant latestSimilarityCalculation = latestSimilarityCalculationOpt.get();
      if (zone.getCalculatedAt() != null && !zone.getCalculatedAt()
          .isBefore(latestSimilarityCalculation)) {
        // the zone is valid, return
        return zone;
      }
    }

    // If it doesn't exist or it's obsolete recompute
    SegmentEfficiencyZone newZone = calculateZone(segmentId);

    // Save and return
    return zoneRepository.save(newZone);
  }

  protected SegmentEfficiencyZone calculateZone(String segmentId) {

    List<Segment> similarSegments = segmentRepository.findSimilarSegmentIdsOrdered(segmentId);
    List<Segment> gradeSegments = segmentRepository.findSegmentsBySameGradeCategory(segmentId);

    Double currentEfficiency = segmentRepository.findById(segmentId)
        .map(Segment::getEfficiencyScore)
        .orElse(null);

    if (currentEfficiency == null) {
      throw new IllegalStateException("Segment has no efficiency score");
    }

    // Efficiencies to be compared
    List<Double> similarEfficiencies = similarSegments.stream()
        .map(Segment::getEfficiencyScore)
        .filter(Objects::nonNull)
        .toList();

    List<Double> gradeEfficiencies = gradeSegments.stream()
        .map(Segment::getEfficiencyScore)
        .filter(Objects::nonNull)
        .toList();

    // Compute zones
    String zoneAmongSimilars = mapPercentileToZone(currentEfficiency, similarEfficiencies);
    String zoneAmongGradeCategory = mapPercentileToZone(currentEfficiency, gradeEfficiencies);

    // Create the record
    SegmentEfficiencyZone zone = new SegmentEfficiencyZone();
    zone.setSegmentId(segmentId);
    zone.setZoneAmongSimilars(zoneAmongSimilars);
    zone.setZoneAmongGradeCategory(zoneAmongGradeCategory);
    zone.setCalculatedAt(Instant.now());

    return zone;
  }

  protected String mapPercentileToZone(double efficiencyScore, List<Double> population) {
    if (population == null || population.isEmpty()) {
      throw new IllegalStateException("No segment similarity data");
    }

    List<Double> sorted = population.stream()
        .sorted()
        .toList();

    int total = sorted.size();
    int countLess = 0;
    for (double value : sorted) {
      if (value <= efficiencyScore) {
        countLess++;
      } else {
        break;
      }
    }

    double percentile = (double) countLess / total;

    if (percentile <= 0.2) {
      return "very_low";
    } else if (percentile <= 0.4) {
      return "low";
    } else if (percentile <= 0.6) {
      return "medium";
    } else if (percentile <= 0.8) {
      return "high";
    } else {
      return "very_high";
    }
  }

}
