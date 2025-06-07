package com.trailmetrics.activities.service;

import com.trailmetrics.activities.dto.PlannedActivityDTO;
import com.trailmetrics.activities.exception.ResourceNotFoundException;
import com.trailmetrics.activities.exception.UnauthorizedAccessException;
import com.trailmetrics.activities.mapper.ActivityMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStatus;
import com.trailmetrics.activities.model.ActivityStatusTracker;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.ActivityStreamRepository;
import com.trailmetrics.activities.repository.SegmentRepository;
import com.trailmetrics.activities.utils.JsonUtils;
import java.io.InputStream;
import java.time.Instant;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@RequiredArgsConstructor
@Service
@Slf4j
public class ActivityService {

  private final ActivityRepository activityRepository;
  private final ActivityStreamRepository activityStreamRepository;
  private final SegmentRepository segmentRepository;
  private final GpxStreamExtractorService gpxStreamExtractorService;
  private final KafkaProducerService kafkaProducerService;

  public Page<Activity> fetchUserActivities(Long userId, Pageable pageable) {
    Page<Activity> page = activityRepository.findByAthleteIdAndIsPlannedIsFalseOrIsPlannedIsNull(
        userId, pageable);
    page.forEach(activity ->
        activity.setStatus(computeStatus(activity.getStatusTracker()))
    );
    return page;
  }

  public Page<Activity> fetchUserPlannedActivities(Long userId, Pageable pageable) {
    Page<Activity> page = activityRepository.findByAthleteIdAndIsPlannedIsTrue(userId, pageable);
    page.forEach(activity ->
        activity.setStatus(computePlanningStatus(activity.getStatusTracker()))
    );
    return page;
  }

  public Activity getUserActivityById(Long activityId, Long userId) {
    Activity activity = activityRepository.findById(activityId)
        .orElseThrow(() -> new ResourceNotFoundException("Activity not found"));
    if (!activity.getAthleteId().equals(userId)) {
      throw new UnauthorizedAccessException("User unauthorized to view this activity");
    }
    activity.setStatus(computeStatus(activity.getStatusTracker()));
    return activity;
  }

  public List<ActivityStream> getActivityStreams(Long activityId) {
    return activityStreamRepository.findByActivityId(activityId);
  }

  public List<Segment> getActivitySegments(Long id) {
    return segmentRepository.findByActivityId(id);
  }

  public ActivityStatus computeStatus(ActivityStatusTracker tracker) {
    if (tracker != null) {
      if (tracker.isNotProcessable()) {
        return ActivityStatus.NOT_PROCESSABLE;
      }
      if (tracker.getSimilarityProcessedAt() != null) {
        return ActivityStatus.SIMILARITY_READY;
      }
      if (tracker.isTerrainStatus() && tracker.isWeatherStatus() && tracker.isSegmentStatus()) {
        return ActivityStatus.DATA_READY;
      }
    }
    return ActivityStatus.CREATED;
  }

  public ActivityStatus computePlanningStatus(ActivityStatusTracker tracker) {
    if (tracker != null) {
      if (tracker.isNotProcessable()) {
        return ActivityStatus.NOT_PROCESSABLE;
      }
      if (tracker.getPredictionExecutedAt() != null) {
        return ActivityStatus.PREDICTION_READY;
      }
      if (tracker.isTerrainStatus() && tracker.isWeatherStatus() && tracker.isSegmentStatus()) {
        return ActivityStatus.DATA_READY;
      }
    }
    return ActivityStatus.CREATED;
  }

  public Activity savePlannedActivity(PlannedActivityDTO dto, MultipartFile gpxFile) {
    try (InputStream inputStream = gpxFile.getInputStream()) {
      // Generate a unique negative id
      long generatedId = -Instant.now().toEpochMilli();
      // Convert DTO to Activity
      Activity activity = ActivityMapper.plannedToEntity(dto, generatedId);

      // Convert the GPX file to ActivityStreams
      List<ActivityStream> streams = gpxStreamExtractorService.extractStreamsFromGpx(inputStream,
          activity);
      activity.setStreams(streams);

      Activity savedActivity = activityRepository.save(activity);

      // Prepare Kafka message payload
      byte[] compressedJson = JsonUtils.prepareCompressedJsonOutputStream(streams);

      log.info("Successfully created planned activity ID: {}", savedActivity.getId());

      // Publish activity processed to Kafka
      kafkaProducerService.publishActivityPlanned(savedActivity.getId(),
          String.valueOf(savedActivity.getAthleteId()),
          savedActivity.getStartDate(),
          compressedJson, savedActivity.getMovingTime());

      return savedActivity;

    } catch (Exception e) {
      throw new RuntimeException("Error saving the Planned Activity", e);
    }
  }
}
