import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import {useLocation, useNavigate} from "react-router-dom";
import { fetchActivityById, fetchActivityStreams, fetchActivitySegments } from "../services/activityService";
import { mapActivityFromApi, CamelCaseActivity } from "../mappers/activityMapper";
import { ActivityStream, Segment } from "../types/activity";
import { MapWithTrack } from "../components/MapWithTrack";
import { CombinedChart } from "../components/CombinedChart";

const ActivityDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const fromPage = (location.state as { fromPage?: number })?.fromPage ?? 0;
  
  const [activity, setActivity] = useState<CamelCaseActivity | null>(null);
  const [streams, setStreams] = useState<ActivityStream | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]); 

  useEffect(() => {
  if (!id) return;

  setLoading(true);

  Promise.all([
    fetchActivityById(id),
    fetchActivityStreams(id),
    fetchActivitySegments(id)
  ])
    .then(([activityData, streamData, segmentData]) => {
      setActivity(mapActivityFromApi(activityData));
      setStreams(streamData);
      setSegments(segmentData);
    })
    .catch((err) => console.error("Error loading activity detail:", err))
    .finally(() => setLoading(false));
}, [id]);


  if (loading) return <p className="p-4 text-sm text-gray-500">Loading...</p>;
  if (!activity) return <p className="p-4 text-sm text-red-500">Activity not found.</p>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">{activity.name}</h1>
      <p className="text-gray-600">{activity.sportType}</p>
      <p>Date: {new Date(activity.startDate).toLocaleString()}</p>
      <p>Distance: {(activity.distance / 1000).toFixed(2)} km</p>
      <p>Duration: {Math.floor(activity.movingTime / 60)} min</p>
      <p>Elevation: {activity.totalElevationGain} m</p>
      {streams && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Activity Map</h2>
          <MapWithTrack latlng={streams.latlng} />
          <h2 className="text-lg font-semibold mb-2">Charts</h2>
          <CombinedChart
          time={streams.time}
          altitude={streams.altitude}
          heartrate={streams.heartrate}
          cadence={streams.cadence}
          speed={streams.speed}
          distance={streams.distance}
          grade={streams.grade}
        /> 
        </div>      
      )}

      {segments.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Segments</h2>
          <ul className="text-sm text-gray-700 space-y-1">
            {segments.map((seg) => (
              <li key={seg.segmentId} className="border-b pb-2">
                <span className="font-medium">#{seg.segmentId}</span>, slope {seg.avgGradient.toFixed(1)}%
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={() => navigate(`/dashboard?page=${fromPage}`)} // back to dashboard preserving the page
        className="mt-6 px-4 py-2 bg-gray-200 text-sm rounded hover:bg-gray-300"
        >
        ← Back to Dashboard
      </button>
    </div>
    
  );
};

export default ActivityDetail;
