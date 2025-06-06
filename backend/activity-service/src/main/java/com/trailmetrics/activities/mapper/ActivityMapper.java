package com.trailmetrics.activities.mapper;

import com.trailmetrics.activities.dto.ActivityDTO;
import com.trailmetrics.activities.dto.PlannedActivityDTO;
import com.trailmetrics.activities.model.Activity;
import org.springframework.stereotype.Service;

@Service
public class ActivityMapper {

  public static Activity convertToEntity(ActivityDTO dto) {
    Activity activity = new Activity();
    activity.setId(dto.getId());
    activity.setName(dto.getName());
    activity.setDistance(dto.getDistance());
    activity.setMovingTime(dto.getMovingTime());
    activity.setTotalElevationGain(dto.getTotalElevationGain());
    activity.setAthleteId(dto.getAthleteId());
    activity.setType(dto.getType());
    activity.setSportType(dto.getSportType());
    activity.setStartDate(dto.getStartDate());
    activity.setMapPolyline(dto.getMapPolyline());
    activity.setAverageSpeed(dto.getAverageSpeed());
    activity.setMaxSpeed(dto.getMaxSpeed());
    activity.setAverageCadence(dto.getAverageCadence());
    activity.setAverageTemp(dto.getAverageTemp());
    activity.setAverageWatts(dto.getAverageWatts());
    activity.setWeightedAverageWatts(dto.getWeightedAverageWatts());
    activity.setHasHeartrate(dto.getHasHeartrate());
    activity.setIsPlanned(false);
    return activity;
  }

  public static ActivityDTO convertToDTO(Activity activity) {
    ActivityDTO dto = new ActivityDTO();
    dto.setId(activity.getId());
    dto.setName(activity.getName());
    dto.setDistance(activity.getDistance());
    dto.setMovingTime(activity.getMovingTime());
    dto.setTotalElevationGain(activity.getTotalElevationGain());
    dto.setAthleteId(activity.getAthleteId());
    dto.setType(activity.getType());
    dto.setSportType(activity.getSportType());
    dto.setStartDate(activity.getStartDate());
    dto.setMapPolyline(activity.getMapPolyline());
    dto.setAverageSpeed(activity.getAverageSpeed());
    dto.setMaxSpeed(activity.getMaxSpeed());
    dto.setAverageCadence(activity.getAverageCadence());
    dto.setAverageTemp(activity.getAverageTemp());
    dto.setAverageWatts(activity.getAverageWatts());
    dto.setWeightedAverageWatts(activity.getWeightedAverageWatts());
    dto.setHasHeartrate(activity.getHasHeartrate());
    dto.setStatus(activity.getStatus() != null ? activity.getStatus().name() : null);

    return dto;
  }

  public static Activity plannedToEntity(PlannedActivityDTO dto, Long generatedId) {
    Activity activity = new Activity();
    activity.setId(generatedId);
    activity.setName(dto.getName());
    activity.setDistance(dto.getDistance());
    activity.setMovingTime(dto.getPlannedDuration()); // planned duration used as movingTime
    activity.setTotalElevationGain(dto.getTotalElevationGain());
    activity.setAthleteId(dto.getAthleteId());
    activity.setType(dto.getType());
    activity.setSportType(dto.getSportType());
    activity.setStartDate(dto.getStartDate());

    // Optional fields are empty
    activity.setMapPolyline(null);
    activity.setAverageSpeed(0);
    activity.setMaxSpeed(0);
    activity.setAverageCadence(null);
    activity.setAverageTemp(null);
    activity.setAverageWatts(null);
    activity.setWeightedAverageWatts(null);
    activity.setHasHeartrate(false);

    // Set isPlanned
    activity.setIsPlanned(true);

    return activity;
  }

  public static PlannedActivityDTO activityToPlannedDTO(Activity activity) {
    PlannedActivityDTO dto = new PlannedActivityDTO();
    dto.setName(activity.getName());
    dto.setDistance(activity.getDistance());
    dto.setPlannedDuration(activity.getMovingTime()); // movingTime diventa plannedDuration
    dto.setTotalElevationGain(activity.getTotalElevationGain());
    dto.setAthleteId(activity.getAthleteId());
    dto.setType(activity.getType());
    dto.setSportType(activity.getSportType());
    dto.setStartDate(activity.getStartDate());
    return dto;
  }

}
