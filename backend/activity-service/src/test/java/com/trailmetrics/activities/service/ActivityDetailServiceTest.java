package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityStreamDTO;
import com.trailmetrics.activities.mapper.ActivityStreamMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;
import org.mockito.MockitoAnnotations;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.client.HttpClientErrorException;

@SpringBootTest
@ActiveProfiles("test")
class ActivityDetailServiceTest {

  @Autowired
  private ActivityDetailService activityDetailService;

  @MockitoBean
  private StravaClient stravaClient;

  @MockitoBean
  private ActivityRepository activityRepository;

  @MockitoBean
  private ActivityStreamRepository activityStreamRepository;

  @MockitoBean
  private KafkaProducerService kafkaProducerService;

  @MockitoBean
  private KafkaRetryService kafkaRetryService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldFetchAndSaveActivityStreams() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 123L;
    String userId = "user-456";

    Activity mockActivity = new Activity();
    mockActivity.setId(activityId);

    ActivityStreamDTO mockStreamDTO = new ActivityStreamDTO();
    List<ActivityStream> mockStreams = List.of(new ActivityStream());

    when(activityRepository.findById(activityId)).thenReturn(Optional.of(mockActivity));
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenReturn(mockStreamDTO);

    // When
    try (MockedStatic<ActivityStreamMapper> mockedMapper = mockStatic(ActivityStreamMapper.class)) {
      mockedMapper.when(
              () -> ActivityStreamMapper.mapStreamsToEntities(mockActivity, mockStreamDTO))
          .thenReturn(mockStreams);

      // When
      activityDetailService.fetchStreamAndUpdateActivity(accessToken, activityId, userId);

      // Then
      verify(activityRepository, times(1)).findById(activityId);
      verify(stravaClient, times(1)).fetchActivityStream(accessToken, activityId);
      verify(activityStreamRepository, times(1)).saveAll(mockStreams);

      // Ensure static method was called
      mockedMapper.verify(
          () -> ActivityStreamMapper.mapStreamsToEntities(mockActivity, mockStreamDTO), times(1));

      // Ensure KafkaProducerService publishes ActivityProcessed once
      verify(kafkaProducerService, times(1)).publishActivityProcessed(activityId);
      verify(kafkaRetryService, never()).scheduleActivityRetry(anyString(), anyLong(), anyInt(),
          any());
    }
  }

  @Test
  void shouldHandleActivityNotFound() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 456L;
    String userId = "user-123";

    when(activityRepository.findById(activityId)).thenReturn(Optional.empty());

    // When & Then
    RuntimeException thrown = assertThrows(
        RuntimeException.class,
        () -> activityDetailService.fetchStreamAndUpdateActivity(accessToken, activityId, userId)
    );

    verify(activityRepository, times(1)).findById(activityId);
    verify(stravaClient, times(1)).fetchActivityStream(accessToken,
        activityId); // API should be called once
    verify(activityStreamRepository, never()).saveAll(any()); // No save should occur

    verify(kafkaProducerService, never()).publishActivityProcessed(
        activityId); // No kafka publishing
    verify(kafkaRetryService, never()).scheduleActivityRetry(anyString(), anyLong(), anyInt(),
        any()); // No rescheduling
  }

  @Test
  void shouldHandleRateLimitAndRetry() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 789L;
    String userId = "user-987";

    HttpHeaders headers = new HttpHeaders();
    headers.add("X-ReadRateLimit-Usage", "110,500"); // Short window exceeded
    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    // When
    when(stravaClient.fetchActivityStream(accessToken, activityId))
        .thenThrow(tooManyRequestsException);
    activityDetailService.fetchStreamAndUpdateActivity(accessToken, activityId, userId);
    // Then
    verify(activityStreamRepository, never()).saveAll(any()); // No save should occur
    verify(kafkaProducerService, never()).publishActivityProcessed(
        activityId); // No Kafka publishing
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId), eq(0),
        eq(tooManyRequestsException)); // Publish activity retry
  }
}
