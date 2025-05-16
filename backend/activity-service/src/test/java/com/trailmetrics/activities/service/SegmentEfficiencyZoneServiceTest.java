package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.model.SegmentEfficiencyZone;
import com.trailmetrics.activities.repository.SegmentEfficiencyZoneRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

class SegmentEfficiencyZoneServiceTest {

  @Mock
  private SegmentRepository segmentRepository;

  @Mock
  private SegmentEfficiencyZoneRepository zoneRepository;

  @InjectMocks
  private SegmentEfficiencyZoneService zoneService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void testNeedsZoneComputation_ValidExistingZoneUpToDate() {
    String segmentId = "seg-1";
    Instant now = Instant.now();

    SegmentEfficiencyZone existingZone = new SegmentEfficiencyZone();
    existingZone.setSegmentId(segmentId);
    existingZone.setCalculatedAt(now);

    when(zoneRepository.findBySegmentId(segmentId)).thenReturn(Optional.of(existingZone));
    when(segmentRepository.findLatestCalculatedAtBySegmentId(segmentId)).thenReturn(
        Optional.of(now.minusSeconds(60)));

    boolean result = zoneService.needsZoneComputation(segmentId);

    assertFalse(result);
  }

  @Test
  void testNeedsZoneComputation_ExpiredZone_ShouldRecalculate() {
    String segmentId = "seg-2";
    Instant oldCalc = Instant.now().minusSeconds(3600);
    Instant similarityCalc = Instant.now();

    SegmentEfficiencyZone expiredZone = new SegmentEfficiencyZone();
    expiredZone.setSegmentId(segmentId);
    expiredZone.setCalculatedAt(oldCalc);

    when(zoneRepository.findBySegmentId(segmentId)).thenReturn(Optional.of(expiredZone));
    when(segmentRepository.findLatestCalculatedAtBySegmentId(segmentId)).thenReturn(
        Optional.of(similarityCalc));

    boolean result = zoneService.needsZoneComputation(segmentId);

    assertTrue(result);
  }

  @Test
  void testNeedsZoneComputation_NoExistingZone_ShouldRecalculate() {
    String segmentId = "seg-3";

    when(zoneRepository.findBySegmentId(segmentId)).thenReturn(Optional.empty());

    boolean result = zoneService.needsZoneComputation(segmentId);

    assertTrue(result);
  }

  @Test
  void testNeedsZoneComputation_NoSimilarityData_ShouldSkip() {
    String segmentId = "seg-4";

    SegmentEfficiencyZone existingZone = new SegmentEfficiencyZone();
    existingZone.setSegmentId(segmentId);
    existingZone.setCalculatedAt(Instant.now());

    when(zoneRepository.findBySegmentId(segmentId)).thenReturn(Optional.of(existingZone));
    when(segmentRepository.findLatestCalculatedAtBySegmentId(segmentId)).thenReturn(
        Optional.empty());

    boolean result = zoneService.needsZoneComputation(segmentId);

    assertFalse(result);
  }
}
