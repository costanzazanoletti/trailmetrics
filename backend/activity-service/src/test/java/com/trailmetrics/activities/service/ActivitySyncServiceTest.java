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
import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.UserPreference;
import com.trailmetrics.activities.repository.ActivityRepository;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockitoAnnotations;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

@SpringBootTest
@ActiveProfiles("test")
class ActivitySyncServiceTest {

  @Autowired
  private ActivitySyncService activitySyncService;

  @MockitoBean
  private StravaClient stravaClient;

  @MockitoBean
  private ActivityRepository activityRepository;

  @MockitoBean
  private KafkaProducerService kafkaProducerService;

  @MockitoBean
  private UserPreferenceService userPreferenceService;


  private static final int INSTANT_SYNC_LIMIT = 10;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.openMocks(this);

    UserPreference mockPreference = new UserPreference();
    mockPreference.setTimezone("Europe/Rome");
    mockPreference.setSyncYears(2);

    when(userPreferenceService.getUserPreference(anyLong())).thenReturn(mockPreference);
  }

  @Test
  void shouldSyncAndSaveActivities() {
    // Given
    String userId = "123";
    String accessToken = "mockAccessToken";
    Instant beforeInstant = Instant.now();

    ActivityDTO activity1 = new ActivityDTO();
    activity1.setId(1L);
    activity1.setName("Activity1");
    activity1.setType("Run");
    activity1.setSport_type("Trail Run");
    activity1.setStart_date(beforeInstant);

    ActivityDTO activity2 = new ActivityDTO();
    activity2.setId(2L);
    activity2.setName("Activity2");
    activity2.setType("Walk");
    activity2.setSport_type("Walk");
    activity2.setStart_date(beforeInstant);

    List<ActivityDTO> mockActivities = Arrays.asList(activity1, activity2);

    Activity savedActivity1 = new Activity();
    savedActivity1.setId(1L);

    Activity savedActivity2 = new Activity();
    savedActivity2.setId(2L);

    // Ensure pagination ends: First call returns activities, second call returns empty list
    when(stravaClient.fetchUserActivities(anyString(), any(), any(), anyInt(), anyInt()))
        .thenReturn(mockActivities)
        .thenReturn(List.of()); // Next page is empty, stopping the loop

    // Ensure `existsById()` returns `false` initially, `true` after save
    when(activityRepository.existsById(anyLong())).thenReturn(false);

    // Mock `save()` so it correctly updates the state
    when(activityRepository.save(any(Activity.class)))
        .thenAnswer(invocation -> {
          Activity savedActivity = invocation.getArgument(0);
          when(activityRepository.existsById(savedActivity.getId())).thenReturn(true);
          return savedActivity;
        });

    when(activityRepository.findById(1L)).thenReturn(java.util.Optional.of(savedActivity1));
    when(activityRepository.findById(2L)).thenReturn(java.util.Optional.of(savedActivity2));

    // When
    activitySyncService.syncUserActivities(userId, accessToken);

    // Then
    verify(activityRepository, times(2)).save(any(Activity.class)); // Ensures only two saves
    verify(kafkaProducerService, times(1)).publishActivityImport(anyLong(),
        eq(userId)); // Ensures only one Kafka message is sent because exceeds instantSyncLimit
  }

  @Test
  void shouldNotSendRealKafkaMessages() {
    verify(kafkaProducerService, never()).publishActivityImport(anyLong(), anyString());
  }

}