import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import {useLocation, useNavigate} from "react-router-dom";
import { fetchActivityById } from "../services/activityService";
import { mapActivityFromApi, CamelCaseActivity } from "../mappers/activityMapper";

const ActivityDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [activity, setActivity] = useState<CamelCaseActivity | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const fromPage = (location.state as { fromPage?: number })?.fromPage ?? 0;

  useEffect(() => {
    if (!id) return;

    fetchActivityById(id)
      .then((data) => {
        const mapped = mapActivityFromApi(data);
        setActivity(mapped);
      })
      .catch((err) => console.error("Error fetching activity:", err))
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
