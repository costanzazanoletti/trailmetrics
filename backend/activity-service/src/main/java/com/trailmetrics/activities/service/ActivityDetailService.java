package com.trailmetrics.activities.service;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.exception.TrailmetricsAuthServiceException;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;

@Service
@Slf4j
@RequiredArgsConstructor
public class ActivityDetailService {


  private final StravaClient stravaClient;
  private final ActivityRepository activityRepository;
  private final ActivityStreamRepository activityStreamRepository;
  private final ActivityStreamParserService activityStreamParserService;
  private final KafkaProducerService kafkaProducerService;
  private final KafkaRetryService kafkaRetryService;
  private final UserAuthService userAuthService;

  public void processActivity(Long activityId, String userId, int retryCount) {
    try {
      log.info("Processing activity ID {} for user {} (Retry: {})", activityId, userId, retryCount);

      // Check if activity exists in database
      Activity activity = activityRepository.findById(activityId)
          .orElseThrow(() -> new RuntimeException("Activity not found: " + activityId));

      // Fetch user access token
      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

      // Process activity (fetch streams)
      List<ActivityStream> activityStreams = fetchStreamAndUpdateActivity(accessToken, activity);

      if (activityStreams != null && !activityStreams.isEmpty()) {

        // Prepare Kafka message payload
        byte[] compressedJson = prepareCompressedJsonOutputStream(activityStreams);

        log.info("Successfully processed activity ID: {}", activityId);

        // Publish activity processed to Kafka
        kafkaProducerService.publishActivityProcessed(activity.getId(), userId,
            activity.getStartDate(),
            compressedJson);
      } else {
        log.info("Activity ID {} already processed or streams are empty", activityId);
      }

    } catch (HttpClientErrorException.TooManyRequests e) {

      log.warn("Rate limit reached for activity ID {}. Retrying (Attempt: {})", activityId,
          retryCount);
      kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, e);


    } catch (TrailmetricsAuthServiceException e) {

      log.error("Error fetching Access Token", e);
      kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, null);

    } catch (Exception e) {

      log.error("Error processing activity ID {}", activityId, e);
      kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, null);

    }
  }


  protected List<ActivityStream> fetchStreamAndUpdateActivity(String accessToken,
      Activity activity) {

    Long activityId = activity.getId();

    // Check if activity streams are in database (avoid duplicates)
    int numStreams = activityStreamRepository.countByActivityId(activityId);
    if (numStreams > 0) {
      log.info("Activity streams for ID {} already in database", activityId);
      return null;
    }

    log.info("Fetching streams for activity ID: {}", activityId);

    try (InputStream jsonStream = stravaClient.fetchActivityStream(accessToken,
        activityId)) {
      // Convert the stream with a parser into an ActivityStream List
      List<ActivityStream> activityStreams = activityStreamParserService.parseActivityStreams(
          jsonStream, activity);

      // Save the streams to database
      activityStreamRepository.saveAll(activityStreams);
      log.info("Saved {} streams for activity ID: {}", activityStreams.size(), activityId);
      return activityStreams;

    } catch (HttpClientErrorException.TooManyRequests e) {
      throw e;
    } catch (Exception e) {
      log.error("Error parsing activity stream for activity ID {}", activityId, e);
      throw new RuntimeException("Failed to parse activity stream", e);
    }


  }

  private byte[] prepareCompressedJsonOutputStream(List<ActivityStream> activityStreams)
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
