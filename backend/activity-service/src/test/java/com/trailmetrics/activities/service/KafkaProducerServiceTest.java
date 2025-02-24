package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;

import com.trailmetrics.activities.dto.ActivityProcessedMessage;
import com.trailmetrics.activities.dto.ActivitySyncMessage;
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

  private static final String ACTIVITY_PROCESSED_TOPIC = "activity-processed-queue";
  private static final String ACTIVITY_SYNC_TOPIC = "activity-sync-queue";

  @Mock(answer = Answers.RETURNS_DEEP_STUBS)
  private KafkaTemplate<String, ActivitySyncMessage> kafkaActivitySyncTemplate;
  @Mock(answer = Answers.RETURNS_DEEP_STUBS)
  private KafkaTemplate<String, ActivityProcessedMessage> kafkaActivityProcessedTemplate;


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
  void shouldSendActivityProcessedEvent() {
    // Given
    Long activityId = 456L;

    // When
    kafkaProducerService.publishActivityProcessed(activityId);

    // Then
    ArgumentCaptor<ActivityProcessedMessage> messageCaptor = ArgumentCaptor.forClass(
        ActivityProcessedMessage.class);
    verify(kafkaActivityProcessedTemplate).send(eq(ACTIVITY_PROCESSED_TOPIC),
        eq(String.valueOf(activityId)),
        messageCaptor.capture());

    ActivityProcessedMessage capturedMessage = messageCaptor.getValue();
    assertEquals(activityId, capturedMessage.getActivityId());
    assertNotNull(capturedMessage.getProcessedAt());
  }
}