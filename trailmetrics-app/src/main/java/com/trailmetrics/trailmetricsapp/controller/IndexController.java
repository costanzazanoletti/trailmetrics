package com.trailmetrics.trailmetricsapp.controller;

import com.trailmetrics.trailmetricsapp.service.StravaActivityService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class IndexController {

  private final StravaActivityService stravaActivityService;

  @Autowired
  public IndexController(StravaActivityService stravaActivityService) {
    this.stravaActivityService = stravaActivityService;
  }

  @GetMapping("/")
  public String login() {
    return "index";
  }

  @GetMapping("/home")
  public String home(Model model, OAuth2AuthenticationToken authentication) {
    // Avvia la sincronizzazione in background
    new Thread(() -> stravaActivityService.fetchAndSaveActivities(authentication)).start();

    model.addAttribute("message", "We are loading your activities, please wait...");
    return "home";
  }
}
