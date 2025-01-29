package com.trailmetrics.trailmetricsapp.service;

import com.trailmetrics.trailmetricsapp.model.Activity;
import com.trailmetrics.trailmetricsapp.repository.ActivityRepository;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class StravaActivityService {

  private final RestTemplate restTemplate;
  private final OAuth2AuthorizedClientService authorizedClientService;
  private final ActivityRepository activityRepository;

  @Value("${strava.api.activities-url}")
  private String activitiesUrl;

  @Value("${strava.allowed-activities}")
  private String allowedActivitiesConfig;

  @Value("${strava.activities-per-page:200}")
  private int activitiesPerPage;

  public StravaActivityService(RestTemplate restTemplate,
      OAuth2AuthorizedClientService authorizedClientService,
      ActivityRepository activityRepository) {
    this.restTemplate = restTemplate;
    this.authorizedClientService = authorizedClientService;
    this.activityRepository = activityRepository;
  }

  public List<Activity> fetchAndSaveActivities(OAuth2AuthenticationToken authentication) {
    OAuth2AuthorizedClient authorizedClient = authorizedClientService.loadAuthorizedClient(
        authentication.getAuthorizedClientRegistrationId(), authentication.getName());

    String accessToken = authorizedClient.getAccessToken().getTokenValue();

    Set<String> allowedActivityTypes = Arrays.stream(allowedActivitiesConfig.split(","))
        .map(String::trim)
        .collect(Collectors.toSet());

    List<Activity> allActivities = new ArrayList<>();
    int page = 1;

    while (true) {
      String url = String.format("%s?access_token=%s&per_page=%d&page=%d", activitiesUrl,
          accessToken,
          activitiesPerPage, page);
      Activity[] activities = restTemplate.getForObject(url, Activity[].class);

      if (activities == null || activities.length == 0) {
        break; // Se la risposta è vuota, interrompiamo la paginazione
      }

      // Filtra solo le attività consentite
      List<Activity> filteredActivities = Arrays.stream(activities)
          .filter(activity -> allowedActivityTypes.contains(activity.getType())
              || allowedActivityTypes.contains(activity.getSportType()))
          .collect(Collectors.toList());

      allActivities.addAll(filteredActivities);
      page++; // Passa alla pagina successiva
    }

    // Ottieni gli ID delle nuove attività sincronizzate
    Set<Long> newActivityIds = allActivities.stream()
        .map(Activity::getId)
        .collect(Collectors.toSet());

    // Trova le attività attualmente nel database
    List<Activity> existingActivities = activityRepository.findAll();

    // Rimuove dal database le attività non più presenti su Strava
    List<Activity> toDelete = existingActivities.stream()
        .filter(activity -> !newActivityIds.contains(activity.getId()))
        .collect(Collectors.toList());

    activityRepository.deleteAll(toDelete);

    // Salva o aggiorna le attività rimanenti
    List<Activity> savedActivities = new ArrayList<>();
    for (Activity activity : allActivities) {
      Optional<Activity> existingActivity = activityRepository.findById(activity.getId());
      if (existingActivity.isPresent()) {
        // Aggiorna i dati dell'attività
        Activity existing = getActivity(activity, existingActivity.get());
      } else {
        // Salva una nuova attività
        savedActivities.add(activityRepository.save(activity));
      }
    }
    return savedActivities;
  }

  private static Activity getActivity(Activity activity, Activity existing) {

    existing.setName(activity.getName());
    existing.setDistance(activity.getDistance());
    existing.setMovingTime(activity.getMovingTime());
    existing.setTotalElevationGain(activity.getTotalElevationGain());
    existing.setType(activity.getType());
    existing.setSportType(activity.getSportType());
    existing.setStartDate(activity.getStartDate());
    return existing;
  }
}
