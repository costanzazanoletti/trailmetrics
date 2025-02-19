package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.UserPreference;
import com.trailmetrics.activities.repository.UserPreferenceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserPreferenceService {

  @Value("${sync.default-sync-years}")
  private Integer defaultSyncYears;

  @Value("${sync.default-zone}")
  private String defaultTimeZone;

  private final UserPreferenceRepository userPreferenceRepository;


  public UserPreference getUserPreference(Long userId) {

    return userPreferenceRepository.findById(userId)
        .orElseGet(() -> {
          UserPreference newPreference = new UserPreference();
          newPreference.setUserId(userId);
          newPreference.setSyncYears(defaultSyncYears);
          newPreference.setTimezone(defaultTimeZone);
          return userPreferenceRepository.save(newPreference);
        });

  }

}
