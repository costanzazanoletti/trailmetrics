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
