package com.trailmetrics.activities.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.dto.ActivityStreamsDTO;
import com.trailmetrics.activities.dto.PlannedActivityDTO;
import com.trailmetrics.activities.dto.SegmentDTO;
import com.trailmetrics.activities.exception.ResourceNotFoundException;
import com.trailmetrics.activities.exception.TrailmetricsAuthServiceException;
import com.trailmetrics.activities.exception.UnauthorizedAccessException;
import com.trailmetrics.activities.mapper.ActivityMapper;
import com.trailmetrics.activities.mapper.ActivityStreamMapper;
import com.trailmetrics.activities.mapper.SegmentMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.response.ApiResponse;
import com.trailmetrics.activities.response.ApiResponseFactory;
import com.trailmetrics.activities.service.ActivityService;
import com.trailmetrics.activities.service.ActivitySyncService;
import com.trailmetrics.activities.service.SegmentEfficiencyZoneService;
import com.trailmetrics.activities.service.UserAuthService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/activities")
@RequiredArgsConstructor
@Slf4j
public class ActivityController {


  private final ActivitySyncService activitySyncService;
  private final UserAuthService userAuthService;
  private final ActivityService activityService;
  private final SegmentMapper segmentMapper;
  private final SegmentEfficiencyZoneService segmentEfficiencyZoneService;
  private final ObjectMapper objectMapper;


  @GetMapping
  public ResponseEntity<ApiResponse<Page<ActivityDTO>>> getActivities(
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "15") int size
  ) {
    try {
      // Get userId
      Long userId = Long.parseLong(getAuthenticatedUserId());
      // Create a Pageable instance using page and size (default sorting by start date descending)
      Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "startDate"));
      // Fetch paginated activities
      Page<Activity> activitiesPage = activityService.fetchUserActivities(userId, pageable);
      Page<ActivityDTO> activityDTOPage = activitiesPage.map(ActivityMapper::convertToDTO);

      // Return the paginated result
      return ApiResponseFactory.ok(activityDTOPage, "Fetched activities");

    } catch (TrailmetricsAuthServiceException e) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    } catch (Exception e) {
      log.error("Failed to fetch activities", e);
      return ApiResponseFactory.error("Failed to fetch activities",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @GetMapping("/sync")
  public ResponseEntity<ApiResponse<Object>> syncActivities() {
    try {
      String userId = getAuthenticatedUserId();
      String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);

      if (accessToken == null) {
        throw new TrailmetricsAuthServiceException("Unauthorized");
      }

      // Synchronize Strava activities
      activitySyncService.syncUserActivities(userId, accessToken);

      return ApiResponseFactory.ok(null, "Synchronization started");
    } catch (TrailmetricsAuthServiceException e) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    } catch (Exception e) {
      return ApiResponseFactory.error("Failed to start activity sync",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @GetMapping("/{activityId}")
  public ResponseEntity<ApiResponse<ActivityDTO>> getActivityDetails(
      @PathVariable Long activityId) {
    try {
      // Fetch activity and check that it belongs to the authenticated user
      Long userId = Long.parseLong(getAuthenticatedUserId());
      Activity activity = activityService.getUserActivityById(activityId, userId);

      ActivityDTO activityDTO = ActivityMapper.convertToDTO(activity);
      return ApiResponseFactory.ok(activityDTO, "Fetched activity details");

    } catch (TrailmetricsAuthServiceException e) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    } catch (UnauthorizedAccessException e) {
      return ApiResponseFactory.error("User doesn't have access to this activity",
          HttpStatus.FORBIDDEN);
    } catch (ResourceNotFoundException e) {
      return ApiResponseFactory.error("Activity not found", HttpStatus.NOT_FOUND);
    } catch (Exception e) {
      log.error("Failed to fetch activity details", e);
      return ApiResponseFactory.error("Failed to fetch activity details",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @GetMapping("/{activityId}/streams")
  public ResponseEntity<ApiResponse<ActivityStreamsDTO>> getActivityStreams(
      @PathVariable Long activityId) {
    try {
      // Fetch activity and check that it belongs to the authenticated user
      Long userId = Long.parseLong(getAuthenticatedUserId());
      Activity activity = activityService.getUserActivityById(activityId, userId);
      List<ActivityStream> streams = activityService.getActivityStreams(activity.getId());

      if (streams.isEmpty()) {
        throw new ResourceNotFoundException("Not found");
      }

      ActivityStreamsDTO streamsDTO = ActivityStreamMapper.mapToDTO(streams);
      return ApiResponseFactory.ok(streamsDTO, "Fetched activity streams");

    } catch (TrailmetricsAuthServiceException e) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    } catch (UnauthorizedAccessException e) {
      return ApiResponseFactory.error("User doesn't have access to this activity",
          HttpStatus.FORBIDDEN);
    } catch (ResourceNotFoundException e) {
      return ApiResponseFactory.error("Activity streams not found", HttpStatus.NOT_FOUND);
    } catch (Exception e) {
      log.error("Failed to fetch activity streams", e);
      return ApiResponseFactory.error("Failed to fetch activity streams",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @GetMapping("/{activityId}/segments")
  public ResponseEntity<ApiResponse<List<SegmentDTO>>> getActivitySegments(
      @PathVariable Long activityId) {
    try {
      // Fetch activity and check that it belongs to the authenticated user
      Long userId = Long.parseLong(getAuthenticatedUserId());
      Activity activity = activityService.getUserActivityById(activityId, userId);

      // Check and compute efficiency zones for activity segments asynchronously
      segmentEfficiencyZoneService.recalculateZonesForActivityAsync(activityId,
          String.valueOf(userId));

      // Fetch activity segments
      List<Segment> segments = activityService.getActivitySegments(activity.getId());

      if (segments.isEmpty()) {
        throw new ResourceNotFoundException("Not found");
      }

      // Prepare response
      List<SegmentDTO> segmentDTOS = segments.stream()
          .map(segmentMapper::toDTO)
          .toList();

      return ApiResponseFactory.ok(segmentDTOS, "Fetched activity segments");

    } catch (TrailmetricsAuthServiceException e) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    } catch (UnauthorizedAccessException e) {
      return ApiResponseFactory.error("User doesn't have access to this activity",
          HttpStatus.FORBIDDEN);
    } catch (ResourceNotFoundException e) {
      return ApiResponseFactory.error("Activity streams not found", HttpStatus.NOT_FOUND);
    } catch (Exception e) {
      log.error("Failed to fetch activity segments", e);
      return ApiResponseFactory.error("Failed to fetch activity segments",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  @PostMapping(value = "/planned", consumes = MediaType.MULTIPART_FORM_DATA_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
  public ResponseEntity<ApiResponse<ActivityDTO>> createPlannedActivity(
      @RequestPart("data") String dataJson,
      @RequestPart("file") MultipartFile gpxFile) {
    try {
      Long userId = Long.parseLong(getAuthenticatedUserId());
      PlannedActivityDTO dto = objectMapper.readValue(dataJson, PlannedActivityDTO.class);
      dto.setAthleteId(userId);
      Activity activity = activityService.savePlannedActivity(dto, gpxFile);
      ActivityDTO responseDto = ActivityMapper.convertToDTO(activity);
      return ResponseEntity.ok(new ApiResponse<>(true, responseDto, "Planned activity created"));
    } catch (Exception e) {
      return ResponseEntity
          .status(HttpStatus.BAD_REQUEST)
          .body(new ApiResponse<>(false, null, "Error: " + e.getMessage()));
    }
  }

  @GetMapping("/planned")
  public ResponseEntity<ApiResponse<Page<ActivityDTO>>> getPlannedActivities(
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "15") int size
  ) {
    try {
      // Get userId
      Long userId = Long.parseLong(getAuthenticatedUserId());
      // Create a Pageable instance using page and size (default sorting by start date descending)
      Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "startDate"));
      // Fetch paginated activities
      Page<Activity> activitiesPage = activityService.fetchUserPlannedActivities(userId, pageable);
      Page<ActivityDTO> activityDTOPage = activitiesPage.map(ActivityMapper::convertToDTO);

      // Return the paginated result
      return ApiResponseFactory.ok(activityDTOPage, "Fetched planned activities");

    } catch (TrailmetricsAuthServiceException e) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    } catch (Exception e) {
      log.error("Failed to fetch planned activities", e);
      return ApiResponseFactory.error("Failed to fetch planned activities",
          HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }


  private String getAuthenticatedUserId() {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    if (authentication == null || !authentication.isAuthenticated()) {
      throw new TrailmetricsAuthServiceException("Unauthorized");
    }
    return authentication.getName();
  }

}
