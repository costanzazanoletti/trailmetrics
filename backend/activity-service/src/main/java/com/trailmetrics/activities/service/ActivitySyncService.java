package com.trailmetrics.activities.service;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.mapper.ActivityMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.UserPreference;
import com.trailmetrics.activities.repository.ActivityRepository;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.List;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.HttpClientErrorException;

@Service
@RequiredArgsConstructor
@Slf4j
public class ActivitySyncService {

  private final UserPreferenceService userPreferenceService;
  private final StravaClient stravaClient;
  private final ActivityRepository activityRepository;
  private final ActivityMapper activityService;
  private final KafkaProducerService kafkaProducerService;
  private final KafkaRetryService kafkaRetryService;
  private final ActivityMapper activityMapper;


  @Value("${strava.api.max-per-page}")
  private int maxPerPage;

  @Value("${strava.api.instant-sync-limit}")
  private int instantSyncLimit;

  @Value("#{'${strava.api.allowed-sport-types}'.split(',')}")
  private List<String> allowedSportTypes;

  /**
   * Fetches activities for a user from Strava, saves them in the database, processes the latest
   * ones instantly, and queues the rest for background processing.
   */
  @Transactional
  public void syncUserActivities(@NonNull String userIdString, @NonNull String accessToken) {

    Long userId = Long.parseLong(userIdString);
    UserPreference preference = userPreferenceService.getUserPreference(userId);

    // Define the sync time range based on user preference
    ZoneId zoneId = ZoneId.of(preference.getTimezone());
    ZonedDateTime beforeDate = ZonedDateTime.now(zoneId);
    ZonedDateTime afterDate = beforeDate.minusYears(preference.getSyncYears());
    Instant beforeInstant = beforeDate.toInstant();
    Instant afterInstant = afterDate.toInstant();

    int page = 1;
    boolean hasMore = true;
    int processedCount = 0;

    while (hasMore) {
      try {
        List<ActivityDTO> activities = stravaClient.fetchUserActivities(accessToken,
            beforeInstant,
            afterInstant,
            page, maxPerPage);

        if (activities.isEmpty()) {
          hasMore = false;
        } else {

          for (ActivityDTO activity : activities) {
            if (!isAllowedActivity(activity)) {
              log.info("Skipping activity ID {} ({}) as it's not in allowed sport types",
                  activity.getId(), activity.getSport_type());
              continue;
            }
            // Save basic metadata for all activities
            saveBasicActivity(userId, activity);

            if (processedCount < instantSyncLimit) {
              log.info("Processing activity ID {} instantly", activity.getId());
              fetchAndUpdateStreams(userIdString, activity.getId(), accessToken);
            } else {
              log.info("Queuing activity ID {} for background sync", activity.getId());
              kafkaProducerService.publishActivityImport(activity.getId(), userIdString);
            }
            processedCount++;
          }
          page++;
        }
      } catch (HttpClientErrorException.TooManyRequests e) {
        log.warn("Rate limit reached for user {}. Requeueing full sync.", userId);

        kafkaRetryService.scheduleUserSyncRetry(userIdString, e);

        return;
      }
    }
  }


  /**
   * Checks if an activity should be processed based on its sport type.
   */
  private boolean isAllowedActivity(ActivityDTO activity) {
    return allowedSportTypes.contains(activity.getType()) || allowedSportTypes.contains(
        activity.getSport_type());
  }

  /**
   * Saves basic metadata for an activity.
   */
  private void saveBasicActivity(Long userId, ActivityDTO activity) {
    if (activityRepository.existsById(activity.getId())) {
      log.debug("Activity ID {} already exists, skipping save.", activity.getId());
      return;
    }

    Activity entity = ActivityMapper.convertToEntity(activity);
    entity.setAthleteId(userId);
    activityRepository.save(entity);
    log.info("Saved basic activity ID {} for user {}", activity.getId(), userId);
  }

  /**
   * Fetches streams (latlng, elevation, cadence, heart rate, etc.) and updates the activity.
   */
  private void fetchAndUpdateStreams(String userId, Long activityId, String accessToken) {
    try {
      Activity activity = activityRepository.findById(activityId)
          .orElseThrow(() -> new RuntimeException("Activity not found: " + activityId));

      log.info("Fetching streams for activity ID {}", activityId);
      // Fetch and save streams from Strava
      stravaClient.fetchActivityStream(accessToken, activityId);

      log.info("Updated activity ID {} with stream data", activityId);

    } catch (HttpClientErrorException.TooManyRequests e) {
      log.warn("Rate limit hit while fetching streams. Queuing activity {} instead.", activityId);
      kafkaProducerService.publishActivityImport(activityId, userId);
    }
  }

}