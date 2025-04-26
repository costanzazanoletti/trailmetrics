package com.trailmetrics.activities.mapper;

import com.trailmetrics.activities.dto.SegmentDTO;
import com.trailmetrics.activities.model.Segment;
import com.trailmetrics.activities.repository.WeatherIconRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class SegmentMapper {

  private final WeatherIconRepository weatherIconRepository;

  public SegmentDTO toDTO(Segment segment) {
    SegmentDTO dto = new SegmentDTO();

    dto.setSegmentId(segment.getSegmentId());
    dto.setActivityId(segment.getActivityId());

    dto.setStartDistance(segment.getStartDistance());
    dto.setEndDistance(segment.getEndDistance());
    dto.setAvgGradient(segment.getAvgGradient());
    dto.setAvgCadence(segment.getAvgCadence());

    dto.setStartLat(segment.getStartLat());
    dto.setEndLat(segment.getEndLat());
    dto.setStartLng(segment.getStartLng());
    dto.setEndLng(segment.getEndLng());

    dto.setStartAltitude(segment.getStartAltitude());
    dto.setEndAltitude(segment.getEndAltitude());

    dto.setStartTime(segment.getStartTime());
    dto.setEndTime(segment.getEndTime());

    dto.setAvgSpeed(segment.getAvgSpeed());
    dto.setElevationGain(segment.getElevationGain());
    dto.setEfficiencyScore(segment.getEfficiencyScore());

    dto.setStartHeartrate(segment.getStartHeartrate());
    dto.setEndHeartrate(segment.getEndHeartrate());
    dto.setAvgHeartrate(segment.getAvgHeartrate());

    dto.setRoadType(segment.getRoadType());
    dto.setSurfaceType(segment.getSurfaceType());

    dto.setTemperature(segment.getTemperature());
    dto.setHumidity(segment.getHumidity());
    dto.setWind(segment.getWind());
    dto.setWeatherId(segment.getWeatherId());
    dto.setWeatherMain(segment.getWeatherMain());
    dto.setWeatherDescription(segment.getWeatherDescription());

    weatherIconRepository.findIconByWeatherId(segment.getWeatherId())
        .ifPresent(dto::setWeatherIcon);

    return dto;
  }
}
