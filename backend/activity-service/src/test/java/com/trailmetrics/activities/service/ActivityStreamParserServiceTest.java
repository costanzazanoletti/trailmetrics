package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;

class ActivityStreamParserServiceTest {

  @InjectMocks
  private ActivityStreamParserService parserService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldParseValidJsonStream() throws Exception {
    InputStream inputStream = getInputStream();
    Activity dummyActivity = new Activity();
    dummyActivity.setId(12345L);

    List<ActivityStream> parsedStreams = parserService.parseActivityStreams(inputStream,
        dummyActivity);

    assertEquals(4, parsedStreams.size());

    for (ActivityStream stream : parsedStreams) {
      assertEquals(12345L, stream.getActivity().getId());
      assertEquals(4, stream.getOriginalSize());
      assertEquals("distance", stream.getSeriesType());
      assertEquals("high", stream.getResolution());
    }

    ActivityStream timeStream = parsedStreams.stream().filter(s -> "time".equals(s.getType()))
        .findFirst().orElseThrow();
    assertEquals("[0,1,2,3]", timeStream.getData());
  }

  @Test
  void shouldHandleInvalidJson() {
    String invalidJson = "{ \"time\": { \"data\": [0, 1, "; // JSON malformato

    InputStream inputStream = new ByteArrayInputStream(
        invalidJson.getBytes(StandardCharsets.UTF_8));
    Activity dummyActivity = new Activity();
    dummyActivity.setId(12345L);

    assertThrows(Exception.class,
        () -> parserService.parseActivityStreams(inputStream, dummyActivity));
  }

  private static InputStream getInputStream() {
    String jsonInput = """
          {
             "time": {
               "data": [0, 1, 2, 3],
               "series_type": "distance",
               "original_size": 4,
               "resolution": "high"
             },
             "latlng": {
               "data": [[46.137134, 8.464204], [46.137118, 8.464177], [46.137102, 8.464150], [46.137090, 8.464120]],
               "series_type": "distance",
               "original_size": 4,
               "resolution": "high"
             },
             "altitude": {
               "data": [661, 663, 665, 668],
               "series_type": "distance",
               "original_size": 4,
               "resolution": "high"
             },
             "velocity_smooth": {
               "data": [2.3, 2.5, 2.6, 2.4],
               "series_type": "distance",
               "original_size": 4,
               "resolution": "high"
             }
           }
        """;

    return new ByteArrayInputStream(jsonInput.getBytes(StandardCharsets.UTF_8));

  }
}