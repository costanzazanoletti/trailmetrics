// components/SimilarSegmentsPanel.tsx
import { Segment } from '../types/activity';
import { useEffect, useState } from 'react';
import { fetchSimilarSegments } from '../services/activityService';
import { formatPace } from '../utils/formatUtils';
import { EfficiencyIcon } from './EfficiencyIcon';

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
              const isSameActivity = seg.activityId === currentActivityId;
              const isCurrent = seg.segmentId === segmentId;

              return (
                <li
                  key={seg.segmentId}
                  onClick={() => {
                    if (!isCurrent) handleClick(seg);
                  }}
                  className={`p-2 rounded border flex justify-between items-center ${
                    isCurrent
                      ? 'bg-blue-100 border-blue-300 text-gray-600 cursor-not-allowed'
                      : 'hover:bg-gray-100 cursor-pointer'
                  }`}
                >
                  <div>
                    <div className="text-sm font-medium">#{seg.segmentId}</div>
                    <div className="text-xs text-gray-600">
                      Grade: {seg.avgGradient?.toFixed(1)}% | Pace:{' '}
                      {seg.avgSpeed ? formatPace(seg.avgSpeed) : 'N/A'}
                      {!isSameActivity && (
                        <span className="ml-2 text-blue-500 text-xs">
                          (other activity)
                        </span>
                      )}
                    </div>
                  </div>
                  <div>
                    {seg.efficiencyZone && (
                      <EfficiencyIcon
                        zone={seg.efficiencyZone}
                        type="efficiency"
                      />
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}
