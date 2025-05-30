package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.dto.PlannedActivityDTO;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockMultipartFile;

class ActivityServiceTest {

  private ActivityRepository activityRepository;
  private GpxStreamExtractorService gpxStreamExtractorService;
  private ActivityStreamRepository activityStreamRepository;
  private SegmentRepository segmentRepository;
  private ActivityService activityService;
  private KafkaProducerService kafkaProducerService;

  @BeforeEach
  void setup() {
    activityRepository = mock(ActivityRepository.class);
    gpxStreamExtractorService = mock(GpxStreamExtractorService.class);
    activityStreamRepository = mock(ActivityStreamRepository.class);
    segmentRepository = mock(SegmentRepository.class);
    kafkaProducerService = mock(KafkaProducerService.class);
    activityService = new ActivityService(activityRepository, activityStreamRepository,
        segmentRepository, gpxStreamExtractorService, kafkaProducerService);
  }

  @Test
  void testSavePlannedActivity_savesCorrectly() {
    // Fake GPX file
    String gpx = """
        <gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
          <trk><trkseg><trkpt lat="46.1" lon="8.2"><ele>1000.0</ele></trkpt></trkseg></trk>
        </gpx>
        """;
    MockMultipartFile file = new MockMultipartFile("file", "test.gpx", "application/gpx+xml",
        gpx.getBytes(StandardCharsets.UTF_8));

    // Input DTO
    PlannedActivityDTO dto = new PlannedActivityDTO();
    dto.setName("Planned Run");
    dto.setAthleteId(1L);
    dto.setDistance(10_000);
    dto.setTotalElevationGain(500);
    dto.setPlannedDuration(3600);
    dto.setSportType("Run");
    dto.setType("planned");
    dto.setStartDate(Instant.now());

    // Mock streams
    Activity dummyActivity = new Activity();
    dummyActivity.setId(-1L);
    ActivityStream dummyStream = new ActivityStream();
    dummyStream.setType("latlng");
    dummyStream.setOriginalSize(1);
    dummyStream.setData("[]");
    when(gpxStreamExtractorService.extractStreamsFromGpx(any(), any())).thenReturn(
        List.of(dummyStream));

    // Mock save
    ArgumentCaptor<Activity> captor = ArgumentCaptor.forClass(Activity.class);
    when(activityRepository.save(captor.capture())).thenAnswer(
        invocation -> invocation.getArgument(0));

    Activity result = activityService.savePlannedActivity(dto, file);

    assertNotNull(result);
    assertEquals("Planned Run", result.getName());
    assertEquals(1, result.getStreams().size());
    assertEquals("latlng", result.getStreams().get(0).getType());
    assertTrue(result.getId() < 0); // negative ID
    assertTrue(result.getIsPlanned());

    verify(activityRepository, times(1)).save(any(Activity.class));
  }
}
