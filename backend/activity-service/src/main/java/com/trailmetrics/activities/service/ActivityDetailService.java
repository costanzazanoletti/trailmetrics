package com.trailmetrics.activities.service;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityStreamDTO;
import com.trailmetrics.activities.exception.TrailmetricsAuthServiceException;
import com.trailmetrics.activities.mapper.ActivityStreamMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;

@Service
@Slf4j
@RequiredArgsConstructor
public class ActivityDetailService {


  private final StravaClient stravaClient;
  private final ActivityRepository activityRepository;
  private final ActivityStreamRepository activityStreamRepository;
  private final KafkaProducerService kafkaProducerService;
  private final KafkaRetryService kafkaRetryService;
  private final UserAuthService userAuthService;

  public void processActivity(Long activityId, String userId, int retryCount) {
    try {
      log.info("Processing activity ID {} for user {} (Retry: {})", activityId, userId, retryCount);

      // Fetch user access token
      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

      // Process activity (fetch streams)
      fetchStreamAndUpdateActivity(accessToken, activityId);

      log.info("Successfully processed activity ID: {}", activityId);

      // Publish activity processed to Kafka
      kafkaProducerService.publishActivityProcessed(activityId);

    } catch (HttpClientErrorException.TooManyRequests e) {

      log.warn("Rate limit reached for activity ID {}. Retrying (Attempt: {})", activityId,
          retryCount);
      kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, e);


    } catch (TrailmetricsAuthServiceException e) {

      log.error("Error fetching Access Token", e);
      kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, null);

    } catch (Exception e) {

      log.error("Error processing activity ID {}", activityId, e);
      kafkaRetryService.scheduleActivityRetry(userId, activityId, retryCount, null);

    }
  }

  private void fetchStreamAndUpdateActivity(String accessToken, Long activityId) {
    log.info("Fetching streams for activity ID: {}", activityId);

    ActivityStreamDTO streamDTO = stravaClient.fetchActivityStream(accessToken, activityId);

    Activity activity = activityRepository.findById(activityId)
        .orElseThrow(() -> new RuntimeException("Activity not found: " + activityId));

    // Delete existing activity streams before saving new ones
    log.info("Deleting existing streams for activity ID: {}", activityId);
    activityStreamRepository.deleteByActivityId(activityId);

    // Convert DTO to List<ActivityStream>
    List<ActivityStream> activityStreams = ActivityStreamMapper.mapStreamsToEntities(activity,
        streamDTO);

    // Save streams to DB
    log.info("Saving {} streams for activity ID: {}", activityStreams.size(), activityId);
    activityStreamRepository.saveAll(activityStreams);

  }


}
