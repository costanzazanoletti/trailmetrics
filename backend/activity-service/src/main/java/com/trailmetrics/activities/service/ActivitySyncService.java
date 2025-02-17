package com.trailmetrics.activities.service;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.UserPreference;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.UserPreferenceRepository;
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

  private final UserPreferenceRepository userPreferenceRepository;
  private final StravaClient stravaClient;
  private final ActivityRepository activityRepository;
  private final KafkaProducerService kafkaProducerService;


  @Value("${sync.default-sync-years}")
  private Integer defaultSyncYears;

  @Value("${sync.default-zone}")
  private String defaultTimeZone;

  @Value("${strava.api.max-per-page}")
  private int maxPerPage;

  @Value("${strava.api.rate-limit-sleep-ms}")
  private int rateLimitSleepMs;

  @Value("${strava.api.rate-limit-threshold}")
  private int rateLimitThreshold;

  @Value("#{'${strava.api.allowed-sport-types}'.split(',')}")
  private List<String> allowedSportTypes;

  private Instant lastRequestTime = Instant.now();
  private int requestCount = 0;

  @Transactional
  public void syncUserActivities(@NonNull String userIdString, @NonNull String accessToken) {

    Long userId = Long.parseLong(userIdString);

    if (accessToken != null) {

      UserPreference preference = userPreferenceRepository.findById(userId)
          .orElseGet(() -> {
            UserPreference newPreference = new UserPreference();
            newPreference.setUserId(userId);
            newPreference.setSyncYears(defaultSyncYears);
            newPreference.setTimezone(defaultTimeZone);
            return userPreferenceRepository.save(newPreference);
          });

      // Start and end date with user's time zone
      ZoneId zoneId = ZoneId.of(preference.getTimezone());
      ZonedDateTime beforeDate = ZonedDateTime.now(zoneId);
      ZonedDateTime afterDate = beforeDate.minusYears(preference.getSyncYears());

      // Convert to Instant (UTC-based timestamp)
      Instant beforeInstant = beforeDate.toInstant();
      Instant afterInstant = afterDate.toInstant();

      log.info("Before: {}", beforeInstant);
      log.info("After: {}", afterDate);

      int page = 1;
      boolean hasMore = true;

      while (hasMore) {
        handleRateLimiting();
        try {
          List<ActivityDTO> activities = stravaClient.fetchUserActivities(accessToken,
              beforeInstant,
              afterInstant,
              page, maxPerPage);
          if (activities.isEmpty()) {
            hasMore = false;
          } else {
            saveAndPublishActivities(userId, activities);
            page++;
          }
        } catch (HttpClientErrorException.TooManyRequests e) {
          log.warn("Strava API rate limit reached. Pausing sync...");
          sleep(rateLimitSleepMs);
        }
      }
    } else {
      throw new RuntimeException("Failed to retrieve Strava access token");
    }
  }

  private void handleRateLimiting() {
    if (requestCount >= rateLimitThreshold) {
      log.info("Rate limit threshold reached, sleeping for cooldown...");
      sleep(rateLimitSleepMs);
      requestCount = 0;
    }
    requestCount++;
    lastRequestTime = Instant.now();
  }

  private void saveAndPublishActivities(Long userId, List<ActivityDTO> activities) {
    activities.stream()
        .filter(a -> allowedSportTypes.contains(a.getType()) || allowedSportTypes.contains(
            a.getSport_type()))
        .map(this::convertToEntity)
        .forEach(activity -> {
          if (!activityRepository.existsById(activity.getId())) {
            activity.setAthleteId(userId);
            activityRepository.save(activity);
            kafkaProducerService.publishActivityImport(activity.getId(), userId);
          }
        });
  }

  private void sleep(int durationMs) {
    try {
      Thread.sleep(durationMs);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }

  private Activity convertToEntity(ActivityDTO dto) {
    Activity activity = new Activity();
    activity.setId(dto.getId());
    activity.setName(dto.getName());
    activity.setDistance(dto.getDistance());
    activity.setMovingTime(dto.getMoving_time());
    activity.setTotalElevationGain(dto.getTotal_elevation_gain());
    activity.setAthleteId(dto.getAthlete_id());
    activity.setType(dto.getType());
    activity.setSportType(dto.getSport_type());
    activity.setStartDate(dto.getStart_date());
    activity.setMapPolyline(dto.getMap_polyline());
    activity.setAverageSpeed(dto.getAverage_speed());
    activity.setMaxSpeed(dto.getMax_speed());
    activity.setAverageCadence(dto.getAverage_cadence());
    activity.setAverageTemp(dto.getAverage_temp());
    activity.setAverageWatts(dto.getAverage_watts());
    activity.setWeightedAverageWatts(dto.getWeighted_average_watts());
    activity.setHasHeartrate(dto.getHas_heartrate());
    return activity;
  }
}