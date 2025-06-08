package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

class GpxStreamExtractorServiceTest {

  private final GpxStreamExtractorService service = new GpxStreamExtractorService();

  @Test
  void testExtractStreamsFromSimpleGpx() {
    ByteArrayInputStream inputStream = getGpxByteArrayInputStream();
    Activity dummyActivity = new Activity();
    dummyActivity.setId(-1L);

    List<ActivityStream> streams = service.extractStreamsFromGpx(inputStream, dummyActivity);

    assertEquals(4, streams.size());

    ActivityStream latlngStream = streams.stream().filter(s -> s.getType().equals("latlng"))
        .findFirst().orElse(null);
    assertNotNull(latlngStream);
    assertTrue(latlngStream.getData().contains("[46.371802,8.427395]"));
    assertEquals(4, latlngStream.getOriginalSize());

    ActivityStream altStream = streams.stream().filter(s -> s.getType().equals("altitude"))
        .findFirst().orElse(null);
    assertNotNull(altStream);
    assertTrue(altStream.getData().contains("1000.0"));
    assertEquals(4, altStream.getOriginalSize());

    ActivityStream distanceStream = streams.stream().filter(s -> s.getType().equals("distance"))
        .findFirst().orElse(null);
    assertNotNull(distanceStream);
    assertEquals(4, distanceStream.getOriginalSize());

    ActivityStream gradeStream = streams.stream().filter(s -> s.getType().equals("grade"))
        .findFirst().orElse(null);
    assertNotNull(gradeStream);
    assertEquals(4, gradeStream.getOriginalSize());

  }

  private static ByteArrayInputStream getGpxByteArrayInputStream() {
    String gpxContent = """
        <?xml version="1.0"?>
        <gpx version="1.1" creator="test" xmlns="http://www.topografix.com/GPX/1/1">
          <trk>
            <trkseg>
              <trkpt lat="46.371550" lon="8.427411"><ele>1000.0</ele></trkpt>
              <trkpt lat="46.371718" lon="8.427394"><ele>1010.0</ele></trkpt>
              <trkpt lat="46.371802" lon="8.427395"><ele>1010.0</ele></trkpt>
              <trkpt lat="46.371920" lon="8.427402"><ele>1010.0</ele></trkpt>
            </trkseg>
          </trk>
        </gpx>
        """;

    ByteArrayInputStream inputStream = new ByteArrayInputStream(
        gpxContent.getBytes(StandardCharsets.UTF_8));
    return inputStream;
  }

}