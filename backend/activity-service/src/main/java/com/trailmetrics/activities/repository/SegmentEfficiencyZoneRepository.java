package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.SegmentEfficiencyZone;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SegmentEfficiencyZoneRepository extends
    JpaRepository<SegmentEfficiencyZone, String> {

  Optional<SegmentEfficiencyZone> findBySegmentId(String segmentId);
}
