package com.trailmetrics.activities.mapper;

import com.trailmetrics.activities.dto.ActivityDTO;
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
    return activity;
  }


}
