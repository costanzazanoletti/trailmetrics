package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.WeatherIcon;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

@Repository
public interface WeatherIconRepository extends JpaRepository<WeatherIcon, Integer> {

  @Query("SELECT w.icon FROM WeatherIcon w WHERE w.weatherId = :weatherId")
  Optional<String> findIconByWeatherId(Integer weatherId);
}
