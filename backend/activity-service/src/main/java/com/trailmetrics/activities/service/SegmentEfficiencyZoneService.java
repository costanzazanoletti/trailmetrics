package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.model.SegmentEfficiencyZone;
import com.trailmetrics.activities.repository.SegmentEfficiencyZoneRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class SegmentEfficiencyZoneService {

  private final SegmentEfficiencyZoneRepository zoneRepository;
  private final SegmentRepository segmentRepository;
  private final KafkaProducerService kafkaProducerService;

  // Cache to avoid duplicate requests: key -> timestamp
  private final ConcurrentMap<String, Instant> recentRequests = new ConcurrentHashMap<>();
  // TTL for each request
  private static final Duration REQUEST_TTL = Duration.ofMinutes(5);

  @Async
  public void recalculateZonesForActivityAsync(Long activityId, String userId) {
    recalculateZonesForActivity(activityId, userId);
  }


  public void recalculateZonesForActivity(Long activityId, String userId) {
    List<Segment> segments = segmentRepository.findByActivityIdOrderBySegmentIdAsc(activityId);

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
    // check if activity has been recently requested
    if (activityRecentlyRequested(activityId, userId)) {
      log.info("Skipped duplicate efficiency zone request for user {}, activity {}", userId,
          activityId);
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

  private boolean activityRecentlyRequested(Long activityId, String userId) {
    String requestKey = getRequestKey(activityId, userId);
    Instant now = Instant.now();
    Instant lastSent = recentRequests.get(requestKey);

    if (lastSent != null && lastSent.plus(REQUEST_TTL).isAfter(now)) {
      return true;
    }
    recentRequests.put(requestKey, now);
    return false;
  }

  // Clean up old request from map
  @Scheduled(fixedRate = 600000) // every 10 minutes
  public void cleanupOldRequests() {
    Instant cutoff = Instant.now().minus(REQUEST_TTL);
    long before = recentRequests.size();
    recentRequests.entrySet().removeIf(entry -> entry.getValue().isBefore(cutoff));
    long after = recentRequests.size();
    log.debug("Cleaned up {} expired requests", (before - after));
  }

  private String getRequestKey(Long activityId, String userId) {
    return userId + "|" + activityId;
  }

}
