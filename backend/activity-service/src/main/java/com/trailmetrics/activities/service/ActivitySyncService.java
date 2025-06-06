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
import java.util.HashSet;
import java.util.List;
import java.util.Set;
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

  @Value("#{'${strava.api.allowed-sport-types}'.split(',')}")
  private List<String> allowedSportTypes;

  /**
   * Fetches activities for a user from Strava, saves them in the database, processes the latest
   * ones instantly, and queues the rest for background processing. Tracks and removes the
   * activities that were in the database but are no longer synchronized.
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

    Set<Long> existingActivityIds = activityRepository.findActivityIdsByAthleteId(userId);
    Set<Long> currentActivityIds = new HashSet<>();

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
                  activity.getId(), activity.getSportType());
              continue;
            }

            currentActivityIds.add(activity.getId());

            if (activityRepository.existsById(activity.getId())) {
              log.debug("Activity ID {} already exists, skipping processing.", activity.getId());
              continue;
            }
            // Save basic metadata for activities not processed yet
            saveBasicActivity(userId, activity);
            // Send Kafka message for activity processing
            log.info("Queuing activity ID {} for background sync", activity.getId());
            kafkaProducerService.publishActivityImport(activity.getId(), userIdString);
          }

          page++;
        }
      } catch (HttpClientErrorException.TooManyRequests e) {
        log.warn("Rate limit reached for user {}. Re-queueing full sync.", userId);
        // Schedule a full sync for the current user
        kafkaRetryService.scheduleUserSyncRetry(userIdString, e);

        return;
      }
    }
    // Identify activities that were in DB but not in the sync
    Set<Long> activitiesToDelete = new HashSet<>(existingActivityIds);
    activitiesToDelete.removeAll(currentActivityIds);
    if (!activitiesToDelete.isEmpty()) {
      // Remove activities from database
      deleteRemovedActivities(activitiesToDelete, userId);
      // publish Kafka message
      kafkaProducerService.publishActivitiesDeleted(String.valueOf(userId), activitiesToDelete);
    }

  }


  /**
   * Checks if an activity should be processed based on its sport type.
   */
  private boolean isAllowedActivity(ActivityDTO activity) {
    return allowedSportTypes.contains(activity.getType()) || allowedSportTypes.contains(
        activity.getSportType());
  }

  /**
   * Saves basic metadata for an activity.
   */
  private void saveBasicActivity(Long userId, ActivityDTO activity) {

    Activity entity = ActivityMapper.convertToEntity(activity);
    entity.setAthleteId(userId);
    activityRepository.save(entity);
    log.info("Saved basic activity ID {} for user {}", activity.getId(), userId);
  }

  /**
   * Deletes from database activities
   */
  private void deleteRemovedActivities(Set<Long> activitiesToDelete, Long userId) {
    if (!activitiesToDelete.isEmpty()) {
      log.info("Found {} activities to delete for user {}", activitiesToDelete.size(), userId);
      // Delete activities from DB and associated streams
      activityRepository.deleteByIdIn(activitiesToDelete);
    }
  }

}
