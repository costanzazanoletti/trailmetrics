package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;

import com.trailmetrics.activities.dto.ActivityProcessedMessage;
import com.trailmetrics.activities.dto.ActivitySyncMessage;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Answers;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.util.ReflectionTestUtils;

class KafkaProducerServiceTest {

  private static final String ACTIVITY_PROCESSED_TOPIC = "activity-stream-queue";
  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";

  @Mock(answer = Answers.RETURNS_DEEP_STUBS)
  private KafkaTemplate<String, ActivitySyncMessage> kafkaActivitySyncTemplate;
  @Mock(answer = Answers.RETURNS_DEEP_STUBS)
  private KafkaTemplate<String, ActivityProcessedMessage> kafkaActivityProcessedTemplate;


  private byte[] compressJson(String json) throws Exception {
    ByteArrayOutputStream compressedStream = new ByteArrayOutputStream();
    try (GZIPOutputStream gzipOutput = new GZIPOutputStream(compressedStream)) {
      gzipOutput.write(json.getBytes(StandardCharsets.UTF_8));
    }
    return compressedStream.toByteArray();
  }


  @InjectMocks
  private KafkaProducerService kafkaProducerService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);

    ReflectionTestUtils.setField(kafkaProducerService, "kafkaActivitySyncTemplate",
        kafkaActivitySyncTemplate);
    ReflectionTestUtils.setField(kafkaProducerService, "kafkaActivityProcessedTemplate",
        kafkaActivityProcessedTemplate);
  }

  @Test
  void shouldPublishActivityImport() {
    // Given
    Long activityId = 1234L;
    String userId = "user-1";

    //When
    kafkaProducerService.publishActivityImport(activityId, userId);

    // Then
    ArgumentCaptor<ActivitySyncMessage> messageCaptor = ArgumentCaptor.forClass(
        ActivitySyncMessage.class);
    verify(kafkaActivitySyncTemplate).send(eq(ACTIVITY_SYNC_TOPIC), eq(String.valueOf(activityId)),
        messageCaptor.capture());

    ActivitySyncMessage capturedMessage = messageCaptor.getValue();
    assertEquals(userId, capturedMessage.getUserId());
    assertEquals(activityId, capturedMessage.getActivityId());
    assertNotNull(capturedMessage.getTimestamp());
  }

  @Test
  void shouldSendActivityProcessedEvent() throws Exception {
    // Given
    Long activityId = 456L;
    String sampleJson = """
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
          }
        }
        """;
    byte[] compressedJson = compressJson(sampleJson);

    // When
    kafkaProducerService.publishActivityProcessed(activityId, compressedJson);

    // Then
    ArgumentCaptor<ActivityProcessedMessage> messageCaptor = ArgumentCaptor.forClass(
        ActivityProcessedMessage.class);
    verify(kafkaActivityProcessedTemplate).send(eq(ACTIVITY_PROCESSED_TOPIC),
        eq(String.valueOf(activityId)),
        messageCaptor.capture());

    ActivityProcessedMessage capturedMessage = messageCaptor.getValue();
    assertEquals(activityId, capturedMessage.getActivityId());
    assertNotNull(capturedMessage.getProcessedAt());
    assertEquals(compressedJson.length, capturedMessage.getCompressedStream().length);
  }
}