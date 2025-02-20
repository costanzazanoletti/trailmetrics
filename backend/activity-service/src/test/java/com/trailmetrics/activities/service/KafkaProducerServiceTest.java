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
  private KafkaTemplate<String, ActivitySyncMessage> kafkaActivitySyncTemplate;


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
    verify(kafkaActivitySyncTemplate).send(eq("activity-sync-queue"), messageCaptor.capture());

    ActivitySyncMessage capturedMessage = messageCaptor.getValue();
    assertEquals(userId, capturedMessage.getUserId());
    assertEquals(activityId, capturedMessage.getActivityId());
    assertNotNull(capturedMessage.getTimestamp());
  }


}