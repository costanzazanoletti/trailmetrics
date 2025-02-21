package com.trailmetrics.activities.service;

import com.trailmetrics.activities.client.StravaClient;
import com.trailmetrics.activities.dto.ActivityStreamDTO;
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


  public void processActivity(String accessToken, Long activityId) {
    log.info("Fetching streams for activity ID: {}", activityId);

    try {

      ActivityStreamDTO streamDTO = stravaClient.fetchActivityStream(accessToken, activityId);

      Activity activity = activityRepository.findById(activityId)
          .orElseThrow(() -> new RuntimeException("Activity not found: " + activityId));

      // Convert DTO to List<ActivityStream>
      List<ActivityStream> activityStreams = ActivityStreamMapper.mapStreamsToEntities(activity,
          streamDTO);

      // Save streams to DB
      log.info("Saving {} streams for activity ID: {}", activityStreams.size(), activityId);
      activityStreamRepository.saveAll(activityStreams);

      // Publish to Kafka the activity processed message to enable metrics computation
      kafkaProducerService.publishActivityProcessed(activityId);

    } catch (HttpClientErrorException.TooManyRequests e) {
      log.warn("Strava API rate limit reached. Checking headers for retry logic...");
      throw e; // Let Kafka retry handling decide the next step
    }
  }


}
