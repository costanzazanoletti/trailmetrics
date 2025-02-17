package com.trailmetrics.activities.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class KafkaProducerService {

  public void publishActivityImport(Long id, Long userId) {
    log.info("Publishing activity import to Kafka for activity {}", id);
  }
}
