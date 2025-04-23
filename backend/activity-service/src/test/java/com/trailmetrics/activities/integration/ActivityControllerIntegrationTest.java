package com.trailmetrics.activities.integration;

import com.trailmetrics.activities.repository.ActivityRepository;
import com.trailmetrics.activities.repository.UserPreferenceRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
@TestPropertySource(locations = "classpath:application-test.properties")
class ActivityControllerIntegrationTest {

  @Autowired
  private MockMvc mockMvc;

  @Autowired
  private ActivityRepository activityRepository;

  @Autowired
  private UserPreferenceRepository userPreferenceRepository;

  @AfterEach
  void cleanup() {
    activityRepository.deleteAll();
    userPreferenceRepository.deleteAll();
  }

  @Test
  void syncActivities_shouldStartSync_whenJwtIsValid() throws Exception {
    /*String fakeJwt = createMockJwt("123");

    mockMvc.perform(get("/api/activities/sync")
            .header("Authorization", "Bearer " + fakeJwt))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.message").value("Synchronization started"));*/
  }

}
