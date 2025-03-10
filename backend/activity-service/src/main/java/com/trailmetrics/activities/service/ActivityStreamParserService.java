package com.trailmetrics.activities.service;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ActivityStreamParserService {


  /**
   * Parses and returns a list of streams
   */
  protected List<ActivityStream> parseActivityStreams(InputStream jsonStream, Activity activity)
      throws Exception {
    JsonFactory jsonFactory = new JsonFactory();
    JsonParser parser = jsonFactory.createParser(jsonStream);

    List<ActivityStream> streams = new ArrayList<>();
    String currentStreamType;

    while (!parser.isClosed()) {
      JsonToken token = parser.nextToken();

      // If we find a FIELD_NAME, save the name (es. "time", "latlng")
      if (token == JsonToken.FIELD_NAME) {
        currentStreamType = parser.getCurrentName();

        // Move the parser to the associated value (START_OBJECT)
        token = parser.nextToken();
        if (token == JsonToken.START_OBJECT) {
          ActivityStream stream = parseStreamData(parser, currentStreamType, activity);

          streams.add(stream);

        }
      }
    }

    parser.close();
    return streams;
  }

  private ActivityStream parseStreamData(JsonParser parser, String streamType, Activity activity)
      throws Exception {
    ActivityStream stream = new ActivityStream();
    stream.setActivity(activity);
    stream.setType(streamType);

    ObjectMapper objectMapper = new ObjectMapper();
    parser.setCodec(objectMapper);
    String jsonData = null;
    String seriesType = null;
    int originalSize = 0;
    String resolution = null;

    while (parser.nextToken() != JsonToken.END_OBJECT) {
      String fieldName = parser.getCurrentName();
      parser.nextToken(); // Move the cursor to the field value

      switch (fieldName) {
        case "data":
          jsonData = objectMapper.writeValueAsString(
              parser.readValueAs(List.class)); // save pure JSON
          break;
        case "series_type":
          seriesType = parser.getText();
          break;
        case "original_size":
          originalSize = parser.getIntValue();
          break;
        case "resolution":
          resolution = parser.getText();
          break;
      }
    }

    stream.setData(jsonData);  // Save json as string
    stream.setSeriesType(seriesType);
    stream.setOriginalSize(originalSize);
    stream.setResolution(resolution);

    return stream;
  }

}
