package com.trailmetrics.activities.mapper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trailmetrics.activities.dto.ActivityStreamDTO;
import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import java.util.ArrayList;
import java.util.List;

public class ActivityStreamMapper {

  private static final ObjectMapper objectMapper = new ObjectMapper();

  /**
   * Convert ActivityStreamDTO to ActivityStream entity.
   */
  public static ActivityStream toEntity(ActivityStreamDTO.StreamData dto, String type,
      Activity activity) {
    if (dto == null) {
      return null;
    }

    ActivityStream entity = new ActivityStream();
    entity.setActivity(activity);
    entity.setType(type);
    entity.setSeriesType(dto.getSeriesType());
    entity.setOriginalSize(dto.getOriginalSize());
    entity.setResolution(dto.getResolution());

    // Convert List<Object> to JSON String
    try {
      entity.setData(objectMapper.writeValueAsString(dto.getData()));
    } catch (JsonProcessingException e) {
      throw new RuntimeException("Error converting data to JSON", e);
    }

    return entity;
  }

  /**
   * Convert ActivityStream entity to ActivityStreamDTO.
   */
  public static ActivityStreamDTO.StreamData toDto(ActivityStream entity) {
    if (entity == null) {
      return null;
    }

    ActivityStreamDTO.StreamData dto = new ActivityStreamDTO.StreamData();
    dto.setSeriesType(entity.getSeriesType());
    dto.setOriginalSize(entity.getOriginalSize());
    dto.setResolution(entity.getResolution());

    // Convert JSON String to List<Object>
    try {
      dto.setData(objectMapper.readValue(entity.getData(), List.class));
    } catch (JsonProcessingException e) {
      throw new RuntimeException("Error converting JSON to List<Object>", e);
    }

    return dto;
  }

  /**
   * Converts ActivityStreamDTO into a List of ActivityStream entities using the mapper.
   */
  public static List<ActivityStream> mapStreamsToEntities(Activity activity,
      ActivityStreamDTO streamDTO) {
    List<ActivityStream> streams = new ArrayList<>();

    if (streamDTO.getLatlng() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getLatlng(), "latlng", activity));
    }
    if (streamDTO.getVelocitySmooth() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getVelocitySmooth(), "velocity_smooth",
          activity));
    }
    if (streamDTO.getGradeSmooth() != null) {
      streams.add(
          ActivityStreamMapper.toEntity(streamDTO.getGradeSmooth(), "grade_smooth", activity));
    }
    if (streamDTO.getCadence() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getCadence(), "cadence", activity));
    }
    if (streamDTO.getHeartrate() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getHeartrate(), "heartrate", activity));
    }
    if (streamDTO.getWatts() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getWatts(), "watts", activity));
    }
    if (streamDTO.getAltitude() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getAltitude(), "altitude", activity));
    }
    if (streamDTO.getDistance() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getDistance(), "distance", activity));
    }
    if (streamDTO.getTime() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getTime(), "time", activity));
    }
    if (streamDTO.getTemp() != null) {
      streams.add(ActivityStreamMapper.toEntity(streamDTO.getTemp(), "temperature", activity));
    }

    return streams;
  }
}
