package com.trailmetrics.activities.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.exception.TrailmetricsAuthServiceException;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.HttpClientErrorException;

class ActivityDetailServiceTest {

  @InjectMocks
  private ActivityDetailService activityDetailService;

  @Mock
  private StravaClient stravaClient;

  @Mock
  private ActivityRepository activityRepository;

  @Mock
  private ActivityStreamRepository activityStreamRepository;

  @Mock
  private ActivityStreamParserService activityStreamParserService;

  @Mock
  private KafkaProducerService kafkaProducerService;

  @Mock
  private KafkaRetryService kafkaRetryService;

  @Mock
  private UserAuthService userAuthService;

  private final String sampleJson = """
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


  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);
  }

  @Test
  void shouldFetchAndSaveActivityStreams() throws Exception {
    // Given
    String accessToken = "mockAccessToken";
    Long activityId = 123L;
    String userId = "user-456";
    int retryCount = 0;

    Activity mockActivity = new Activity();
    mockActivity.setId(activityId);
    mockActivity.setStartDate(Instant.now().minusSeconds(999999999L));

    InputStream jsonStream = new ByteArrayInputStream(sampleJson.getBytes(StandardCharsets.UTF_8));
    ActivityStream mockActivityStream = new ActivityStream();
    mockActivityStream.setType("latlng");
    mockActivityStream.setData(
        "[[46.137134, 8.464204], [46.137118, 8.464177], [46.137102, 8.464150]]");

    List<ActivityStream> mockStreams = List.of(mockActivityStream);

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);
    when(activityRepository.findById(activityId)).thenReturn(Optional.of(mockActivity));
    when(activityStreamRepository.countByActivityId(activityId)).thenReturn(0);
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenReturn(jsonStream);
    when(activityStreamParserService.parseActivityStreams(jsonStream, mockActivity)).thenReturn(
        mockStreams);

    // When
    when(activityStreamParserService.parseActivityStreams(any(), any())).thenReturn(mockStreams);
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(activityStreamRepository, times(1)).saveAll(mockStreams);
    verify(kafkaProducerService, times(1)).publishActivityProcessed(eq(mockActivity.getId()),
        eq(userId), eq(mockActivity.getStartDate()),
        any(byte[].class), anyInt());
    verify(kafkaRetryService, never()).scheduleActivityRetry(anyString(), anyLong(), anyInt(),
        any());
  }

  @Test
  void shouldHandleRateLimitAndRetry() {
    Long activityId = 789L;
    String userId = "user-987";
    int retryCount = 0;
    String accessToken = "mockAccessToken";

    Activity mockActivity = new Activity();
    mockActivity.setId(activityId);

    HttpHeaders headers = new HttpHeaders();
    headers.add("X-ReadRateLimit-Usage", "110,500");
    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    when(activityRepository.findById(activityId)).thenReturn(Optional.of(mockActivity));
    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenThrow(
        tooManyRequestsException);

    // When
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId),
        eq(retryCount), eq(tooManyRequestsException));
    verify(kafkaProducerService, never()).publishActivityProcessed(anyLong(), anyString(), any(),
        any(), anyInt());
  }

  @Test
  void shouldHandleAuthServiceExceptionAndRetry() {
    Long activityId = 101L;
    String userId = "user-111";
    int retryCount = 0;

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenThrow(
        new TrailmetricsAuthServiceException("Failed to retrieve token"));

    // When
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId),
        eq(retryCount), eq(null));
    verify(kafkaProducerService, never()).publishActivityProcessed(anyLong(), anyString(), any(),
        any(), anyInt());
  }

  @Test
  void shouldHandleParsingErrorAndRetry() throws Exception {
    Long activityId = 202L;
    String userId = "user-222";
    int retryCount = 0;
    String accessToken = "mockAccessToken";

    Activity mockActivity = new Activity();
    mockActivity.setId(activityId);

    InputStream jsonStream = new ByteArrayInputStream(sampleJson.getBytes(StandardCharsets.UTF_8));

    when(userAuthService.fetchAccessTokenFromAuthService(userId)).thenReturn(accessToken);
    when(activityRepository.findById(activityId)).thenReturn(Optional.of(mockActivity));
    when(activityStreamRepository.countByActivityId(activityId)).thenReturn(0);
    when(stravaClient.fetchActivityStream(accessToken, activityId)).thenReturn(jsonStream);
    when(activityStreamParserService.parseActivityStreams(any(), any())).thenThrow(
        new RuntimeException("Parsing error"));

    // When
    activityDetailService.processActivity(activityId, userId, retryCount);

    // Then
    verify(kafkaRetryService, times(1)).scheduleActivityRetry(eq(userId), eq(activityId),
        eq(retryCount), eq(null));
    verify(kafkaProducerService, never()).publishActivityProcessed(anyLong(), anyString(), any(),
        any(), anyInt());
  }
}
