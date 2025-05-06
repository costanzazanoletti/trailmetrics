import {
  useParams,
  useLocation,
  useNavigate,
  useSearchParams,
} from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import { shouldPollForZones } from '../utils/efficiencyUtils';
import {
  fetchActivityById,
  fetchActivityStreams,
  fetchActivitySegments,
} from '../services/activityService';
import {
  mapActivityFromApi,
  CamelCaseActivity,
} from '../mappers/activityMapper';
import { ActivityStream, Segment, ActivityStatus } from '../types/activity';
import { MapWithTrack } from '../components/MapWithTrack';
import { CombinedChart } from '../components/CombinedChart';
import { EfficiencyLegend } from '../components/EfficiencyZoneLegend';
import { ActivityHeader } from '../components/ActivityHeader';
import { SegmentList } from '../components/SegmentList';
import { SimilarSegmentsPanel } from '../components/SimilarSegmentsPanel';
import { ActivityStatusIcon } from '../components/ActivityStatusIcon';

const ActivityDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState<CamelCaseActivity | null>(null);
  const [streams, setStreams] = useState<ActivityStream | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [needsPolling, setNeedsPolling] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState<number | null>(null);
  const [selectedSegmentForSimilar, setSelectedSegmentForSimilar] =
    useState<Segment | null>(null);

  const navigate = useNavigate();
  const location = useLocation();

  const fromPage = (location.state as { fromPage?: number })?.fromPage ?? 0;

  const preselectedSegmentId = searchParams.get('segment');

  const segmentRefs = useRef<Map<string, HTMLLIElement>>(new Map());

  const handleSelectSegment = (seg: Segment | null) => {
    setSelectedSegment(seg);
    if (!seg || seg.segmentId !== selectedSegment?.segmentId) {
      setSelectedSegmentForSimilar(null);
    }
  };

  const handleShowSimilar = async (segment: Segment) => {
    try {
      setSelectedSegment(segment);
      setSelectedSegmentForSimilar(segment);
    } catch (error) {
      console.error('Failed to load similar segments', error);
    }
  };

  useEffect(() => {
    if (selectedSegment) {
      const ref = segmentRefs.current.get(selectedSegment.segmentId);
      if (ref) {
        ref.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedSegment]);

  useEffect(() => {
    if (!id) return;

    setLoading(true);

    Promise.all([
      fetchActivityById(id),
      fetchActivityStreams(id),
      fetchActivitySegments(id),
    ])
      .then(([activityData, streamData, segmentData]) => {
        setActivity(mapActivityFromApi(activityData));
        setStreams(streamData);
        setSegments(segmentData);

        // Pre-select
        if (preselectedSegmentId) {
          const match = segmentData.find(
            (s: Segment) => s.segmentId === preselectedSegmentId
          );
          if (match) setSelectedSegment(match);
        }

        // Check if needs polling
        if (shouldPollForZones(segmentData)) {
          setNeedsPolling(true);
        } else {
          setNeedsPolling(false);
        }
      })
      .catch((err) => console.error('Error loading activity detail:', err))
      .finally(() => setLoading(false));
  }, [id]);

  // Automatic polling if we need the zones
  useEffect(() => {
    if (!needsPolling) return;

    const interval = setInterval(() => {
      fetchActivitySegments(id!)
        .then((segmentData) => {
          setSegments(segmentData);

          const someWithoutZone = segmentData.some(
            (s: Segment) =>
              s.efficiencyZone == null || s.gradeEfficiencyZone == null
          );

          if (!someWithoutZone) {
            setNeedsPolling(false); // Fermiamo polling
            clearInterval(interval);
          }
        })
        .catch((err) => console.error('Error reloading segments:', err));
    }, 5000); // ogni 5 secondi

    return () => clearInterval(interval);
  }, [needsPolling, id]);

  if (loading) return <p className="p-4 text-sm text-gray-500">Loading...</p>;

  if (!activity || activity.status !== ActivityStatus.SIMILARITY_READY)
    return (
      <p className="p-4 text-sm text-red-500">
        Activity not found or not processed.
      </p>
    );

  return (
    <div className="container mx-auto p-4">
      {/* Header */}
      <ActivityHeader activity={activity} />

      {/* Legend */}
      <EfficiencyLegend />

      {/* Body */}
      <div className="flex flex-col md:flex-row gap-6">
        {/* Left: Segments */}
        <SegmentList
          segments={segments}
          selectedSegment={selectedSegment}
          onSelect={handleSelectSegment}
          onShowSimilar={handleShowSimilar}
          segmentRefs={segmentRefs}
        />

        {/* Right: Map + Chart */}
        <div className="flex-1 min-w-0 flex flex-col gap-6">
          {streams && (
            <>
              {/* Map */}
              <div className="h-[400px]">
                <MapWithTrack
                  latlng={streams.latlng}
                  segments={segments}
                  selectedSegmentId={selectedSegment?.segmentId}
                  onSelectSegment={(seg) => handleSelectSegment(seg)}
                  highlightIndex={highlightIndex}
                />
              </div>
              {/* Similar segments panel  */}
              {selectedSegmentForSimilar && (
                <SimilarSegmentsPanel
                  segmentId={selectedSegmentForSimilar.segmentId}
                  currentActivityId={selectedSegmentForSimilar.activityId}
                  gradeCategory={selectedSegmentForSimilar.gradeCategory}
                  onClose={() => setSelectedSegmentForSimilar(null)}
                  onSegmentClick={(seg) => setSelectedSegment(seg)}
                />
              )}
              {/* Combined Chart */}
              <CombinedChart
                time={streams.time}
                altitude={streams.altitude}
                heartrate={streams.heartrate}
                cadence={streams.cadence}
                speed={streams.speed}
                distance={streams.distance}
                grade={streams.grade}
                onHoverIndexChange={setHighlightIndex}
                highlightIndex={highlightIndex}
                segments={segments}
                selectedSegmentId={selectedSegment?.segmentId}
                onSegmentClick={setSelectedSegment}
              />
            </>
          )}
        </div>
      </div>

      {/* Back button */}
      <div className="mt-8">
        <button
          onClick={() => navigate(`/dashboard?page=${fromPage}`)}
          className="px-4 py-2 bg-gray-200 text-sm rounded hover:bg-gray-300"
        >
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default ActivityDetail;
