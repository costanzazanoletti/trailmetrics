package com.trailmetrics.activities.controller;

import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.mapper.ActivityMapper;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.response.ApiResponse;
import com.trailmetrics.activities.response.ApiResponseFactory;
import com.trailmetrics.activities.service.ActivityService;
import com.trailmetrics.activities.service.ActivitySyncService;
import com.trailmetrics.activities.service.UserAuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/activities")
@RequiredArgsConstructor
public class ActivityController {


  private final ActivitySyncService activitySyncService;
  private final UserAuthService userAuthService;
  private final ActivityService activityService;


  @GetMapping
  public ResponseEntity<ApiResponse<Page<ActivityDTO>>> getActivities(
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "15") int size
  ) {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    if (authentication == null || !authentication.isAuthenticated()) {
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }

    Long userId = Long.valueOf(authentication.getName());
    try {
      // Create Pageable instance using page and size (default sorting by start date descending)
      Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "startDate"));
      // Fetch paginated activities
      Page<Activity> activitiesPage = activityService.fetchUserActivities(userId, pageable);
      Page<ActivityDTO> activityDTOPage = activitiesPage.map(ActivityMapper::convertToDTO);
      
      // Return the paginated result
      return ApiResponseFactory.ok(activityDTOPage, "Fetched activities");
    } catch (Exception e) {
      return ApiResponseFactory.error("Failed to fetch activities");
    }
  }

  @GetMapping("/sync")
  public ResponseEntity<ApiResponse<Object>> syncActivities() {
    Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
    if (authentication == null || !authentication.isAuthenticated()) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    }

    String userId = authentication.getName();
    String accessToken = userAuthService.fetchAccessTokenFromAuthService(userId);
    if (accessToken == null) {
      return ApiResponseFactory.error("Unauthorized", HttpStatus.UNAUTHORIZED);
    }

    // Synchronize Strava activities
    activitySyncService.syncUserActivities(userId, accessToken);

    return ApiResponseFactory.ok(null, "Synchronization started");
  }
}
