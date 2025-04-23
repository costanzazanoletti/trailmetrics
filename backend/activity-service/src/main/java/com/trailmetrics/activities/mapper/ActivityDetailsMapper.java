package com.trailmetrics.activities.mapper;

import com.trailmetrics.activities.dto.ActivityDetailsDTO;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ActivityDetailsMapper {

  public static ActivityDetailsDTO toDetailsDto(Activity activity, List<ActivityStream> streams) {
    ActivityDetailsDTO dto = new ActivityDetailsDTO();
    dto.setId(activity.getId());
    dto.setName(activity.getName());
    dto.setDistance(activity.getDistance());
    dto.setMovingTime(activity.getMovingTime());
    dto.setTotalElevationGain(activity.getTotalElevationGain());
    dto.setSportType(activity.getSportType());
    dto.setStartDate(activity.getStartDate());

    for (ActivityStream stream : streams) {
      if ("latlng".equals(stream.getType())) {
        dto.setLatlng(stream.getDataAsList());
      } else if ("altitude".equals(stream.getType())) {
        dto.setAltitude(stream.getDataAsList());
      }
    }

    return dto;
  }
}
