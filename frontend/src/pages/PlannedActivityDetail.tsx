import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useEffect, useState, useRef, useMemo } from 'react';
import {
  fetchActivityById,
  fetchActivityStreams,
  fetchActivitySegments,
} from '../services/activityService';
import {
  mapActivityFromApi,
  CamelCaseActivity,
} from '../mappers/activityMapper';
import { ActivityStream, Segment } from '../types/activity';
import { ActivityHeader } from '../components/ActivityHeader';
import { SegmentList } from '../components/SegmentList';
import { CombinedChart } from '../components/CombinedChart';
import { MapWithTrack } from '../components/MapWithTrack';

const PlannedActivityDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [activity, setActivity] = useState<CamelCaseActivity | null>(null);
  const [streams, setStreams] = useState<ActivityStream | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [highlightIndex, setHighlightIndex] = useState<number | null>(null);
  const [segmentWindow, setSegmentWindow] = useState<[number, number] | null>(
    null
  );

  const navigate = useNavigate();
  const location = useLocation();
  const fromPage = (location.state as { fromPage?: number })?.fromPage ?? 0;

  const segmentRefs = useRef<Map<string, HTMLLIElement>>(new Map());

  useEffect(() => {
    if (!id) return;

    Promise.all([
      fetchActivityById(id),
      fetchActivityStreams(id),
      fetchActivitySegments(id),
    ])
      .then(([activityData, streamData, segmentData]) => {
        setActivity(mapActivityFromApi(activityData));
        setStreams(streamData);
        setSegments(segmentData);
      })
      .catch((err) => console.error('Error loading planned activity:', err));
  }, [id]);

  useEffect(() => {
    if (selectedSegment && streams?.distance) {
      const startIdx = streams.distance.findIndex(
        (d) => d >= selectedSegment.startDistance
      );
      const endIdx = streams.distance.findIndex(
        (d) => d >= selectedSegment.endDistance
      );
      setHighlightIndex(startIdx);
      setSegmentWindow([startIdx, endIdx]);
    } else {
      setSegmentWindow(null);
    }
  }, [selectedSegment, streams?.distance]);

  useEffect(() => {
    if (selectedSegment) {
      const ref = segmentRefs.current.get(selectedSegment.segmentId);
      if (ref) {
        ref.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedSegment]);

  const interpolatedTime = useMemo(() => {
    if (!streams?.distance || segments.length === 0) return [];

    return streams.distance.map((d) => {
      const seg = segments.find(
        (s) => s.startDistance <= d && s.endDistance >= d
      );
      if (!seg?.startTime || !seg?.endTime) return 0;

      const progress =
        (d - seg.startDistance) / (seg.endDistance - seg.startDistance);
      const interpolated =
        seg.startTime + progress * (seg.endTime - seg.startTime);
      return Math.round(interpolated);
    });
  }, [streams?.distance, segments]);

  if (!activity || !streams) {
    return <p className="p-4 text-sm text-gray-500">Loading...</p>;
  }

  return (
    <div className="container mx-auto p-4">
      <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded text-orange-800 text-sm">
        Viewing details of a <strong>planned activity</strong>
      </div>
      <ActivityHeader activity={activity} planned />

      <div className="flex flex-col md:flex-row gap-6">
        <SegmentList
          segments={segments}
          selectedSegment={selectedSegment}
          onSelect={setSelectedSegment}
          onShowSimilar={() => {}}
          segmentRefs={segmentRefs}
          variant="planned"
        />

        <div className="flex-1 min-w-0 flex flex-col gap-6">
          <div className="h-[400px]">
            <MapWithTrack
              latlng={streams.latlng}
              segments={segments}
              selectedSegmentId={selectedSegment?.segmentId}
              onSelectSegment={setSelectedSegment}
              highlightIndex={highlightIndex}
            />
          </div>
          <CombinedChart
            time={interpolatedTime}
            altitude={streams.altitude}
            distance={streams.distance}
            grade={streams.grade}
            segments={segments}
            selectedSegmentId={selectedSegment?.segmentId}
            onSegmentClick={setSelectedSegment}
            onHoverIndexChange={setHighlightIndex}
            highlightIndex={highlightIndex}
            segmentWindow={segmentWindow}
            variant="altimetryOnly"
          />
        </div>
      </div>

      <div className="mt-8">
        <button
          onClick={() => navigate(`/planning?page=${fromPage}`)}
          className="px-4 py-2 bg-gray-200 text-sm rounded hover:bg-gray-300"
        >
          ← Back to Planning
        </button>
      </div>
    </div>
  );
};

export default PlannedActivityDetail;
