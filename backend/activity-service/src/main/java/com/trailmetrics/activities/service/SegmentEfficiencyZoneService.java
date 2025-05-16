package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.model.SegmentEfficiencyZone;
import com.trailmetrics.activities.repository.SegmentEfficiencyZoneRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class SegmentEfficiencyZoneService {

  private final SegmentEfficiencyZoneRepository zoneRepository;
  private final SegmentRepository segmentRepository;
  private final KafkaProducerService kafkaProducerService;

  @Async
  public void recalculateZonesForActivityAsync(Long activityId, String userId) {
    recalculateZonesForActivity(activityId, userId);
  }


  public void recalculateZonesForActivity(Long activityId, String userId) {
    List<Segment> segments = segmentRepository.findByActivityId(activityId);

    if (segments.isEmpty()) {
      log.info("No segments found for activity {}", activityId);
      return;
    }

    // Collect the ids of segments that need computation
    Set<String> missingZoneSegmentIds = segments.stream()
        .filter(s -> needsZoneComputation(s.getSegmentId()))
        .map(Segment::getSegmentId)
        .collect(Collectors.toSet());

    if (missingZoneSegmentIds.isEmpty()) {
      log.info("All segments already have valid efficiency zones for activity {}", activityId);
      return;
    }

    kafkaProducerService.publishEfficiencyZoneRequest(userId, missingZoneSegmentIds);
  }

  protected boolean needsZoneComputation(String segmentId) {
    Optional<SegmentEfficiencyZone> existing = zoneRepository.findBySegmentId(segmentId);

    if (existing.isEmpty()) {
      return true; // never computed
    }

    Optional<Instant> latestSimilarityCalculationOpt = segmentRepository.findLatestCalculatedAtBySegmentId(
        segmentId);
    if (latestSimilarityCalculationOpt.isEmpty()) {
      return false; // not computable
    }

    Instant latestSimilarity = latestSimilarityCalculationOpt.get();
    Instant calculatedAt = existing.get().getCalculatedAt();

    return calculatedAt == null || calculatedAt.isBefore(latestSimilarity);
  }


}
