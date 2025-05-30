package com.trailmetrics.activities.utils;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trailmetrics.activities.model.ActivityStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPOutputStream;

public class JsonUtils {

  public static byte[] prepareCompressedJsonOutputStream(List<ActivityStream> activityStreams)
      throws IOException {
    ByteArrayOutputStream jsonOutputStream = new ByteArrayOutputStream();

    try (OutputStreamWriter writer = new OutputStreamWriter(jsonOutputStream,
        StandardCharsets.UTF_8);
        JsonGenerator jsonGenerator = new ObjectMapper().createGenerator(writer)) {

      jsonGenerator.writeStartArray();
      for (ActivityStream stream : activityStreams) {
        jsonGenerator.writeStartObject();
        jsonGenerator.writeStringField("type", stream.getType());
        jsonGenerator.writeFieldName("data");

        jsonGenerator.writeRawValue(stream.getData());
        jsonGenerator.writeEndObject();
      }
      jsonGenerator.writeEndArray();
      jsonGenerator.flush();
    }

    // Compress json output stream
    ByteArrayOutputStream compressedStream = new ByteArrayOutputStream();
    try (GZIPOutputStream gzipOutput = new GZIPOutputStream(compressedStream)) {
      gzipOutput.write(jsonOutputStream.toByteArray());
    }

    return compressedStream.toByteArray();
  }
}
