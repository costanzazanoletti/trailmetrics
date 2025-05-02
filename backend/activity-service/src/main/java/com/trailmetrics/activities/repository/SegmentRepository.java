package com.trailmetrics.activities.repository;

import com.trailmetrics.activities.model.Segment;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface SegmentRepository extends JpaRepository<Segment, String> {

  List<Segment> findByActivityId(Long activityId);

  @Query("""
          SELECT s
          FROM Segment s
          WHERE s.segmentId IN (
              SELECT ss.id.similarSegmentId
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

  @Query("""
        SELECT s
        FROM Segment s
        WHERE s.segmentId IN (
            SELECT ss.id.similarSegmentId
            FROM SegmentSimilarity ss
            WHERE ss.id.segmentId = :segmentId
            ORDER BY ss.rank
        )
      """)
  List<Segment> findTopSimilarSegments(String segmentId);

  @Query("""
          SELECT s FROM Segment s
          WHERE s.gradeCategory = :gradeCategory AND s.segmentId <> :excludeSegmentId
          ORDER BY s.efficiencyScore DESC NULLS LAST
      """)
  List<Segment> findTopByGradeCategory(@Param("gradeCategory") Double gradeCategory,
      @Param("excludeSegmentId") String excludeSegmentId,
      Pageable pageable);

}
