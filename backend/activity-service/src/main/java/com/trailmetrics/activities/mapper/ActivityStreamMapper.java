package com.trailmetrics.activities.mapper;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.trailmetrics.activities.dto.ActivityStreamsDTO;
import com.trailmetrics.activities.model.ActivityStream;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ActivityStreamMapper {

  private static final ObjectMapper objectMapper = new ObjectMapper();

  public static ActivityStreamsDTO mapToDTO(List<ActivityStream> streams) {
    ActivityStreamsDTO dto = new ActivityStreamsDTO();

    for (ActivityStream stream : streams) {
      String type = stream.getType();
      try {
        switch (type) {
          case "latlng" -> {
            // Expecting List of [lat, lng] pairs
            List<List<Double>> latlng = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setLatlng(latlng);
          }
          case "altitude" -> {
            List<Double> alt = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setAltitude(alt);
          }
          case "heartrate" -> {
            List<Integer> hr = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setHeartrate(hr);
          }
          case "distance" -> {
            List<Double> dist = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setDistance(dist);
          }
          case "time" -> {
            List<Integer> time = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setTime(time);
          }
          case "cadence" -> {
            List<Integer> cad = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setCadence(cad);
          }
          case "grade_smooth" -> {
            List<Double> grade = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setGrade(grade);
          }
          case "velocity_smooth" -> {
            List<Double> speed = objectMapper.readValue(
                stream.getData(),
                new TypeReference<>() {
                }
            );
            dto.setSpeed(speed);
          }
          default -> {
            // Ignore other types by now
          }
        }
      } catch (Exception e) {
        throw new RuntimeException("Failed to parse stream of type: " + type, e);
      }
    }

    return dto;
  }
}
