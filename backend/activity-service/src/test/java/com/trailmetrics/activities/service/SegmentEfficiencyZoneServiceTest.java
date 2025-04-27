package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.model.SegmentEfficiencyZone;
import com.trailmetrics.activities.repository.SegmentEfficiencyZoneRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.time.Instant;
import java.util.List;
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
  void testMapPercentileToZone() {
    List<Double> efficiencies = List.of(0.8, 0.9, 1.0, 1.1, 1.2);

    assertEquals("very_low", zoneService.mapPercentileToZone(0.8, efficiencies));
    assertEquals("low", zoneService.mapPercentileToZone(0.9, efficiencies));
    assertEquals("medium", zoneService.mapPercentileToZone(1.0, efficiencies));
    assertEquals("high", zoneService.mapPercentileToZone(1.1, efficiencies));
    assertEquals("very_high", zoneService.mapPercentileToZone(1.2, efficiencies));
  }

  @Test
  void testGetOrCalculateZone_ValidExistingZone() {
    String segmentId = "seg-1";
    SegmentEfficiencyZone existingZone = new SegmentEfficiencyZone();
    existingZone.setSegmentId(segmentId);
    existingZone.setCalculatedAt(Instant.now());

    when(zoneRepository.findBySegmentId(segmentId)).thenReturn(Optional.of(existingZone));
    when(segmentRepository.findLatestCalculatedAtBySegmentId(segmentId))
        .thenReturn(Optional.of(existingZone.getCalculatedAt().minusSeconds(60)));

    SegmentEfficiencyZone result = zoneService.getOrCalculateZone(segmentId);

    assertEquals(existingZone, result);
    verify(zoneRepository, never()).save(any());
  }

  @Test
  void testGetOrCalculateZone_ExpiredZone_ShouldRecalculate() {
    String segmentId = "seg-2";
    Segment segment = new Segment();
    segment.setSegmentId(segmentId);
    segment.setEfficiencyScore(1.2);

    String similarSegmentId = "seg-20";
    Segment similarSegment = new Segment();
    similarSegment.setSegmentId(similarSegmentId);
    similarSegment.setEfficiencyScore(2.9);

    SegmentEfficiencyZone expiredZone = new SegmentEfficiencyZone();
    expiredZone.setSegmentId(segmentId);
    expiredZone.setCalculatedAt(Instant.now().minusSeconds(3600)); // very old

    SegmentRepository segmentSimilarityRepo = segmentRepository;
    when(zoneRepository.findBySegmentId(segmentId)).thenReturn(Optional.of(expiredZone));
    when(segmentSimilarityRepo.findLatestCalculatedAtBySegmentId(segmentId))
        .thenReturn(Optional.of(Instant.now()));

    when(segmentRepository.findById(segmentId)).thenReturn(Optional.of(segment));
    when(segmentSimilarityRepo.findSimilarSegmentIdsOrdered(segmentId)).thenReturn(
        List.of(similarSegment));
    when(segmentRepository.findSegmentsBySameGradeCategory(segmentId)).thenReturn(
        List.of(similarSegment));

    SegmentEfficiencyZone newZone = new SegmentEfficiencyZone();
    newZone.setSegmentId(segmentId);

    when(zoneRepository.save(any())).thenReturn(newZone);

    SegmentEfficiencyZone result = zoneService.getOrCalculateZone(segmentId);

    assertNotNull(result);
    assertEquals(segmentId, result.getSegmentId());
    verify(zoneRepository).save(any());
  }

  @Test
  void testGetOrCalculateZone_NoSimilarityData_ShouldThrowException() {
    String segmentId = "seg-3";
    Segment segment = new Segment();
    segment.setSegmentId(segmentId);
    segment.setEfficiencyScore(1.2);

    SegmentEfficiencyZone existingZone = new SegmentEfficiencyZone();
    existingZone.setSegmentId(segmentId);
    existingZone.setCalculatedAt(Instant.now());

    when(segmentRepository.findById(segmentId)).thenReturn(Optional.of(segment));
    when(zoneRepository.findById(segmentId)).thenReturn(Optional.of(existingZone));
    when(segmentRepository.findLatestCalculatedAtBySegmentId(segmentId))
        .thenReturn(Optional.empty()); // no similarity data!

    IllegalStateException ex = assertThrows(IllegalStateException.class, () -> {
      zoneService.getOrCalculateZone(segmentId);
    });

    assertTrue(ex.getMessage().contains("No segment similarity data"));
  }
}
