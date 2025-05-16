import { Segment } from '../types/activity';
import { SegmentCard } from './SegmentCard';
import { RefObject } from 'react';

interface SegmentListProps {
  segments: Segment[];
  selectedSegment: Segment | null;
  onSelect: (segment: Segment) => void;
  onShowSimilar: (segment: Segment) => void;
  segmentRefs: RefObject<Map<string, HTMLLIElement>>;
}

export function SegmentList({
  segments,
  selectedSegment,
  onSelect,
  onShowSimilar,
  segmentRefs,
}: SegmentListProps) {
  return (
    <div className="md:w-1/4 bg-gray-50 rounded-md p-4 h-[870px] overflow-y-auto">
      <h2 className="text-lg text-gray-600 font-semibold mb-4">Segments</h2>

      {segments.length > 0 ? (
        <ul className="space-y-2 text-sm text-gray-700">
          {segments
            .slice()
            .sort((a, b) => {
              const idA = parseInt(a.segmentId.split('-')[1] ?? '0', 10);
              const idB = parseInt(b.segmentId.split('-')[1] ?? '0', 10);
              return idA - idB;
            })
            .map((seg) => (
              <li
                key={seg.segmentId}
                ref={(el) => {
                  if (el) segmentRefs.current?.set(seg.segmentId, el);
                }}
              >
                <SegmentCard
                  segment={seg}
                  isSelected={selectedSegment?.segmentId === seg.segmentId}
                  onSelect={onSelect}
                  onShowSimilar={() => onShowSimilar(seg)}
                  variant={'full'}
                />
              </li>
            ))}
        </ul>
      ) : (
        <p className="text-gray-500 text-sm">No segments available</p>
      )}
    </div>
  );
}
