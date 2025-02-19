package com.trailmetrics.activities.service;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
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

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldFetchAndSaveActivityStreams() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 123L;

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
      activityDetailService.processActivity(accessToken, activityId);

      // Then
      verify(activityRepository, times(1)).findById(activityId);
      verify(stravaClient, times(1)).fetchActivityStream(accessToken, activityId);
      verify(activityStreamRepository, times(1)).saveAll(mockStreams);

      // Ensure static method was called
      mockedMapper.verify(
          () -> ActivityStreamMapper.mapStreamsToEntities(mockActivity, mockStreamDTO), times(1));
    }
  }

  @Test
  void shouldHandleActivityNotFound() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 456L;

    when(activityRepository.findById(activityId)).thenReturn(Optional.empty());

    // When & Then
    RuntimeException thrown = assertThrows(
        RuntimeException.class,
        () -> activityDetailService.processActivity(accessToken, activityId)
    );

    verify(activityRepository, times(1)).findById(activityId);
    verify(stravaClient, times(1)).fetchActivityStream(accessToken,
        activityId); // API should be called once
    verify(activityStreamRepository, never()).saveAll(any()); // No save should occur
  }

  @Test
  void shouldHandleRateLimitAndRetry() {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 789L;

    HttpHeaders headers = new HttpHeaders();
    headers.add("X-RateLimit-Usage", "100,500"); // Rate limit exceeded

    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    when(stravaClient.fetchActivityStream(accessToken, activityId))
        .thenThrow(tooManyRequestsException);

    // When & Then
    assertThrows(HttpClientErrorException.TooManyRequests.class,
        () -> activityDetailService.processActivity(accessToken, activityId));

    verify(stravaClient, times(1)).fetchActivityStream(accessToken, activityId);
    verify(activityStreamRepository, never()).saveAll(any()); // No save should occur
  }
}
