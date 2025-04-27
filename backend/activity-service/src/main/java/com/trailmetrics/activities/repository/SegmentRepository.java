package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.Segment;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface SegmentRepository extends JpaRepository<Segment, String> {

  List<Segment> findByActivityId(Long activityId);

  @Query("""
          SELECT s
          FROM Segment s
          WHERE s.segmentId IN (
              SELECT ss.id.segmentId
              FROM SegmentSimilarity ss
              WHERE ss.id.segmentId = :segmentId
              ORDER BY ss.rank ASC
          )
      """)
  List<Segment> findSimilarSegmentIdsOrdered(String segmentId);

  @Query("""
          SELECT s
          FROM Segment s
          WHERE s.gradeCategory IS NOT NULL
            AND s.gradeCategory = (
                SELECT gradeCategory
                FROM Segment
                WHERE segmentId = :segmentId
            )
      """)
  List<Segment> findSegmentsBySameGradeCategory(String segmentId);

  @Query("""
          SELECT MAX(ss.calculatedAt)
          FROM SegmentSimilarity ss
          WHERE ss.id.segmentId = :segmentId
      """)
  Optional<Instant> findLatestCalculatedAtBySegmentId(String segmentId);

}
