package com.trailmetrics.activities.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anySet;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.UserPreference;
import com.trailmetrics.activities.repository.ActivityRepository;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;

class ActivitySyncServiceTest {

  @InjectMocks
  private ActivitySyncService activitySyncService;

  @Mock
  private StravaClient stravaClient;

  @Mock
  private ActivityRepository activityRepository;

  @Mock
  private KafkaProducerService kafkaProducerService;

  @Mock
  private UserPreferenceService userPreferenceService;

  @Mock
  private KafkaRetryService kafkaRetryService;

  @Mock
  private ActivitySyncLogService activitySyncLogService;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);

    UserPreference mockPreference = new UserPreference();
    mockPreference.setTimezone("Europe/Rome");
    mockPreference.setSyncYears(2);

    when(userPreferenceService.getUserPreference(anyLong())).thenReturn(mockPreference);

    List<String> mockAllowedSportTypes = new ArrayList<>(
        List.of("Run", "Trail Run", "Walk", "Hike"));
    ReflectionTestUtils.setField(activitySyncService, "maxPerPage", 100);
    ReflectionTestUtils.setField(activitySyncService, "allowedSportTypes", mockAllowedSportTypes);
  }

  @Test
  void shouldSyncAndSaveActivitiesAndLogThem() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    ActivityDTO activity1 = new ActivityDTO();
    activity1.setId(1L);
    activity1.setName("Activity1");
    activity1.setType("Run");

    ActivityDTO activity2 = new ActivityDTO();
    activity2.setId(2L);
    activity2.setName("Activity2");
    activity2.setType("Walk");

    List<ActivityDTO> mockActivities = Arrays.asList(activity1, activity2);
    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(mockActivities)
        .thenReturn(List.of());

    when(activityRepository.existsById(anyLong())).thenReturn(false);
    when(activityRepository.save(any(Activity.class)))
        .thenAnswer(invocation -> invocation.getArgument(0));

    activitySyncService.syncUserActivities(userId, accessToken);

    verify(activityRepository, times(2)).save(any(Activity.class));
    verify(kafkaProducerService, times(2)).publishActivityImport(anyLong(), eq(userId));
    verify(activitySyncLogService, times(1))
        .recordSyncLog(eq(123L), eq(Set.of(1L, 2L)), eq(Set.of()));
  }

  @Test
  void shouldHandleActivityDeletionAndLogThem() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    ActivityDTO activity1 = new ActivityDTO();
    activity1.setId(1L);
    activity1.setType("Run");

    ActivityDTO activity2 = new ActivityDTO();
    activity2.setId(2L);
    activity2.setType("Walk");

    List<ActivityDTO> mockActivities = Arrays.asList(activity1, activity2);
    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(mockActivities)  // First page with activities
        .thenReturn(List.of());  // Empty list on second page (end of data)

    // Existing activity IDs in the database (activity 1 is already in DB, activity 3 was deleted)
    when(activityRepository.findActivityIdsByAthleteId(anyLong()))
        .thenReturn(new HashSet<>(Arrays.asList(1L, 3L)));  // ID 3 will be removed

    when(activityRepository.existsById(anyLong())).thenReturn(false);
    when(activityRepository.save(any(Activity.class)))
        .thenAnswer(invocation -> invocation.getArgument(0));

    activitySyncService.syncUserActivities(userId, accessToken);

    // Verify that activity 3 is deleted because it's no longer in the sync data
    verify(activityRepository, times(1)).deleteByIdIn(eq(new HashSet<>(Set.of(3L))));
    verify(activityRepository, times(2)).save(any(Activity.class));
    verify(kafkaProducerService, times(2)).publishActivityImport(anyLong(), eq(userId));
    verify(activitySyncLogService, times(1))
        .recordSyncLog(eq(123L), eq(Set.of(1L, 2L)), eq(Set.of(3L)));
  }

  @Test
  void shouldNotDeleteExistingActivitiesAndLogNoChanges() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    ActivityDTO activity1 = new ActivityDTO();
    activity1.setId(1L);
    activity1.setType("Run");

    ActivityDTO activity2 = new ActivityDTO();
    activity2.setId(2L);
    activity2.setType("Walk");

    List<ActivityDTO> mockActivities = Arrays.asList(activity1, activity2);
    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(mockActivities)
        .thenReturn(List.of());

    // Existing activity IDs in the database
    when(activityRepository.findActivityIdsByAthleteId(anyLong()))
        .thenReturn(new HashSet<>(Arrays.asList(1L, 2L)));  // No deletions

    when(activityRepository.existsById(anyLong())).thenReturn(false);
    when(activityRepository.save(any(Activity.class)))
        .thenAnswer(invocation -> invocation.getArgument(0));

    activitySyncService.syncUserActivities(userId, accessToken);

    // Verify no deletion of activities
    verify(activityRepository, never()).deleteByIdIn(any());
    verify(activityRepository, times(2)).save(any(Activity.class));
    verify(kafkaProducerService, times(2)).publishActivityImport(anyLong(), eq(userId));
    verify(activitySyncLogService, times(1))
        .recordSyncLog(eq(123L), eq(Set.of(1L, 2L)), eq(Set.of()));
  }

  @Test
  void shouldHandleEmptyActivityListAndLogNoChanges() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(List.of());

    activitySyncService.syncUserActivities(userId, accessToken);

    verify(activityRepository, never()).save(any(Activity.class));
    verify(kafkaProducerService, never()).publishActivityImport(anyLong(), anyString());
    verify(activitySyncLogService, times(1))
        .recordSyncLog(eq(123L), eq(Set.of()), eq(Set.of()));
  }

  @Test
  void shouldNotSaveExistingActivitiesAndLogNoChanges() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    ActivityDTO activity1 = new ActivityDTO();
    activity1.setId(1L);
    activity1.setType("Run");

    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(List.of(activity1))
        .thenReturn(List.of());

    when(activityRepository.existsById(1L)).thenReturn(true);

    activitySyncService.syncUserActivities(userId, accessToken);

    verify(activityRepository, never()).save(any(Activity.class));
    verify(kafkaProducerService, never()).publishActivityImport(anyLong(), anyString());
    verify(activitySyncLogService, times(1))
        .recordSyncLog(eq(123L), eq(Set.of()), eq(Set.of()));
  }

  @Test
  void shouldSkipActivitiesWithInvalidSportTypeAndLogNoChanges() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    ActivityDTO activity1 = new ActivityDTO();
    activity1.setId(1L);
    activity1.setType("Cycling"); // Not in allowed sports

    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(List.of(activity1))
        .thenReturn(List.of());

    activitySyncService.syncUserActivities(userId, accessToken);

    verify(activityRepository, never()).save(any(Activity.class));
    verify(kafkaProducerService, never()).publishActivityImport(anyLong(), anyString());
    verify(activitySyncLogService, times(1))
        .recordSyncLog(eq(123L), eq(Set.of()), eq(Set.of()));
  }

  @Test
  void shouldHandleRateLimitAndRetryFullSyncAndNotLogChanges() {
    String userId = "123";
    String accessToken = "mockAccessToken";

    HttpHeaders headers = new HttpHeaders();
    headers.add("X-ReadRateLimit-Usage", "110,500");
    HttpClientErrorException tooManyRequestsException = HttpClientErrorException.create(
        HttpStatus.TOO_MANY_REQUESTS, "Too Many Requests", headers, null, StandardCharsets.UTF_8
    );

    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenThrow(tooManyRequestsException);

    activitySyncService.syncUserActivities(userId, accessToken);

    verify(kafkaRetryService, times(1)).scheduleUserSyncRetry(eq(userId), any());
    verify(kafkaRetryService, never()).scheduleActivityRetry(anyString(), anyLong(), anyInt(),
        any());
    verify(kafkaProducerService, never()).publishActivityImport(anyLong(), anyString());
    verify(activityRepository, never()).save(any(Activity.class));
    verify(activitySyncLogService, never()).recordSyncLog(anyLong(), anySet(), anySet());
  }
}
