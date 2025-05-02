import { useEffect, useState } from 'react';
import { Segment } from '../types/activity';
import {
  fetchSimilarSegments,
  fetchTopSegmentsByGrade,
} from '../services/activityService';
import { SegmentCard } from './SegmentCard';
import { getGradeCategoryRange } from '../utils/formatUtils';

interface SimilarSegmentsPanelProps {
  segmentId: string;
  currentActivityId: number;
  gradeCategory: number;
  onClose: () => void;
  onSegmentClick?: (segment: Segment) => void;
}

export function SimilarSegmentsPanel({
  segmentId,
  currentActivityId,
  gradeCategory,
  onClose,
  onSegmentClick,
}: SimilarSegmentsPanelProps) {
  const [loading, setLoading] = useState(true);
  const [similarSegments, setSimilarSegments] = useState<Segment[]>([]);
  const [topGradeSegments, setTopGradeSegments] = useState<Segment[]>([]);
  const [needsPolling, setNeedsPolling] = useState(false);

  const fetchAll = async () => {
    try {
      const [similar, grade] = await Promise.all([
        fetchSimilarSegments(segmentId),
        fetchTopSegmentsByGrade(segmentId),
      ]);
      setSimilarSegments(similar);
      setTopGradeSegments(grade);

      const missingZones = [...similar, ...grade].some(
        (s) => !s.efficiencyZone || !s.gradeEfficiencyZone
      );

      setNeedsPolling(missingZones);
    } catch (err) {
      console.error('Error loading segment data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchAll();
  }, [segmentId]);

  useEffect(() => {
    if (!needsPolling) return;

    const interval = setInterval(() => {
      fetchAll();
    }, 2000);

    return () => clearInterval(interval);
  }, [needsPolling]);

  const handleClick = (seg: Segment) => {
    if (seg.segmentId === segmentId) return;
    if (seg.activityId === currentActivityId) {
      onSegmentClick?.(seg);
    } else {
      window.open(
        `/activities/${seg.activityId}?segment=${seg.segmentId}`,
        '_blank'
      );
    }
  };

  const renderSegmentList = (segments: Segment[]) => (
    <ul className="space-y-2 text-sm">
      {segments.map((seg) => {
        const isCurrent = seg.segmentId === segmentId;
        return (
          <li key={seg.segmentId}>
            <SegmentCard
              segment={seg}
              isSelected={isCurrent}
              onSelect={() => {
                if (!isCurrent) handleClick(seg);
              }}
              variant="compact"
              currentActivityId={currentActivityId}
            />
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="mt-6 p-4 border rounded bg-white shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Similar Segments</h3>
        <button
          onClick={onClose}
          className="text-sm text-blue-600 hover:underline"
        >
          Close
        </button>
      </div>

      {loading ? (
        <p className="text-sm text-gray-500">Loading similar segments...</p>
      ) : similarSegments.length === 0 ? (
        <p className="text-sm text-gray-500">No similar segments found.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium mb-2">Top 5 by similarity</h4>
            {renderSegmentList(
              similarSegments
                .filter((s) => s.efficiencyScore !== null)
                .sort(
                  (a, b) => (b.efficiencyScore ?? 0) - (a.efficiencyScore ?? 0)
                )
                .slice(0, 5)
            )}
          </div>

          <div>
            <h4 className="text-sm font-medium mb-2">
              Top 5 by grade from {getGradeCategoryRange(gradeCategory)[0]}% to{' '}
              {getGradeCategoryRange(gradeCategory)[1]}%
            </h4>
            {renderSegmentList(topGradeSegments.slice(0, 5))}
          </div>
        </div>
      )}
    </div>
  );
}
