package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;

import com.trailmetrics.activities.dto.ActivitySyncMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.kafka.core.KafkaTemplate;

class KafkaProducerServiceTest {

  @Mock
  private KafkaTemplate<String, ActivitySyncMessage> kafkaTemplate;

  @InjectMocks
  private KafkaProducerService kafkaProducerService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldPublishActivityImport() {
    Long activityId = 1234L;
    String userId = "user-1";

    kafkaProducerService.publishActivityImport(activityId, userId);

    ArgumentCaptor<ActivitySyncMessage> messageCaptor = ArgumentCaptor.forClass(
        ActivitySyncMessage.class);
    verify(kafkaTemplate).send(eq("activity-sync-queue"), messageCaptor.capture());

    ActivitySyncMessage capturedMessage = messageCaptor.getValue();
    assertEquals(userId, capturedMessage.getUserId());
    assertEquals(activityId, capturedMessage.getActivityId());
    assertEquals(0, capturedMessage.getRetryCount());
    assertNotNull(capturedMessage.getTimestamp());
  }

  @Test
  void shouldPublishActivityRetry() {
    String userId = "user-1";
    Long activityId = 123L;
    int retryCount = 2;

    kafkaProducerService.publishActivityRetry(userId, activityId, retryCount);

    ArgumentCaptor<ActivitySyncMessage> messageCaptor = ArgumentCaptor.forClass(
        ActivitySyncMessage.class);
    verify(kafkaTemplate).send(eq("activity-sync-queue"), messageCaptor.capture());

    ActivitySyncMessage capturedMessage = messageCaptor.getValue();
    assertEquals(userId, capturedMessage.getUserId());
    assertEquals(activityId, capturedMessage.getActivityId());
    assertEquals(retryCount, capturedMessage.getRetryCount());
    assertNotNull(capturedMessage.getTimestamp());
  }

}