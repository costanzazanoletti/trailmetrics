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
  private final KafkaProducerService kafkaProducerService;
  private final KafkaRetryService kafkaRetryService;


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
        log.info("Fetching page {} of activities for user {}", page, userIdString);
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

            // process immediately the first activities
            if (processedCount < instantSyncLimit) {
              try {
                log.info("Processing activity ID {} instantly", activity.getId());
                fetchAndUpdateStreams(activity.getId(), accessToken);
              } catch (HttpClientErrorException.TooManyRequests e) {
                // if the rate limit is hit re-queue the activity
                log.warn("Rate limit reached for activity ID {}. Re-queueing activity sync.",
                    activity.getId());
                kafkaRetryService.scheduleActivityRetry(userIdString, activity.getId(), 0, e);
              }
            } else {
              log.info("Queuing activity ID {} for background sync", activity.getId());
              kafkaProducerService.publishActivityImport(activity.getId(), userIdString);
            }
            processedCount++;
          }
          page++;
        }
      } catch (HttpClientErrorException.TooManyRequests e) {
        log.warn("Rate limit reached for user {}. Re-queueing full sync.", userId);

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
  private void fetchAndUpdateStreams(Long activityId, String accessToken) {

    activityRepository.findById(activityId)
        .orElseThrow(() -> new RuntimeException("Activity not found: " + activityId));

    log.info("Fetching streams for activity ID {}", activityId);
    // Fetch and save streams from Strava
    stravaClient.fetchActivityStream(accessToken, activityId);

    log.info("Updated activity ID {} with stream data", activityId);

  }

}