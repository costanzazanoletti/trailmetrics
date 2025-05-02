// components/SimilarSegmentsPanel.tsx
import { Segment } from '../types/activity';
import { useEffect, useState } from 'react';
import { fetchSimilarSegments } from '../services/activityService';
import { SegmentCard } from './SegmentCard';

interface SimilarSegmentsPanelProps {
  segmentId: string;
  currentActivityId: number;
  onClose: () => void;
  onSegmentClick?: (segment: Segment) => void;
}

export function SimilarSegmentsPanel({
  segmentId,
  currentActivityId,
  onClose,
  onSegmentClick,
}: SimilarSegmentsPanelProps) {
  const [loading, setLoading] = useState(true);
  const [similarSegments, setSimilarSegments] = useState<Segment[]>([]);

  useEffect(() => {
    fetchSimilarSegments(segmentId)
      .then((data) => setSimilarSegments(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [segmentId]);

  const topEfficiency = [...similarSegments]
    .filter((s) => s.efficiencyScore !== null)
    .sort((a, b) => (b.efficiencyScore ?? 0) - (a.efficiencyScore ?? 0))
    .slice(0, 5);

  const handleClick = (seg: Segment) => {
    if (seg.segmentId === segmentId) return; // already selected
    if (seg.activityId === currentActivityId) {
      onSegmentClick?.(seg);
    } else {
      window.open(
        `/activities/${seg.activityId}?segment=${seg.segmentId}`,
        '_blank'
      );
    }
  };

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
        <>
          <p className="text-sm mb-2 text-gray-600 font-medium">
            Top 5 by efficiency:
          </p>
          <ul className="space-y-2 text-sm">
            {topEfficiency.map((seg) => {
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
        </>
      )}
    </div>
  );
}
