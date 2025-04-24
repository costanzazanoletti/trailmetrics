import { useEffect, useState } from "react";
import {useSearchParams, Link} from "react-router-dom";
import { fetchActivities } from "../services/activityService";
import { mapActivityFromApi, CamelCaseActivity } from "../mappers/activityMapper";
import {formatDuration} from "../utils/timeFormat";

const Dashboard = () => {
  const [activities, setActivities] = useState<CamelCaseActivity[]>([]);
  const [searchParams] = useSearchParams();
  const initialPage = parseInt(searchParams.get("page") || "0", 10);
  const [page, setPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  // Navigation functions
  const goToNextPage = () => {
    if (page < totalPages - 1) {
      setPage((prev) => prev + 1);
    }
  };

  const goToPreviousPage = () => {
    if (page > 0) {
      setPage((prev) => prev - 1);
    }
  };

  useEffect(() => {
  setIsLoading(true);

  fetchActivities(page, 10)
    .then((res) => {
      const mapped = res.content.map(mapActivityFromApi);
      setActivities(mapped);
      setTotalPages(res.totalPages);
    })
    .catch((err) => console.error("Fetch error:", err))
    .finally(() => {
      setIsLoading(false);
    });
  }, [page]);


  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-6">Your Running Activities</h1>

      {isLoading ? (
        <p className="text-center text-sm text-gray-500 py-10">Loading activities...</p>
      ) : activities.length === 0 ? (
        <p>No activities found.</p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white rounded shadow">
              <thead>
                <tr className="bg-gray-100 text-left text-sm text-gray-700">
                  <th className="px-4 py-2">Sport</th>
                  <th className="px-4 py-2">Date</th>
                  <th className="px-4 py-2">Name</th>
                  <th className="px-4 py-2">Distance (km)</th>
                  <th className="px-4 py-2">Time</th>
                  <th className="px-4 py-2">Elevation (m)</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((activity) => (
                  <tr key={activity.id} className="border-t hover:bg-gray-50 text-sm">
                    <td className="px-4 py-2">{activity.sportType}</td>
                    <td className="px-4 py-2">
                      {new Date(activity.startDate).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2">
                      <Link 
                        to={`/activities/${activity.id}`} 
                        state={{fromPage: page}}
                        className="text-blue-600 hover:underline"
                      >
                        {activity.name}
                      </Link>
                    </td>
                    <td className="px-4 py-2">{(activity.distance / 1000).toFixed(2)}</td>
                    <td className="px-4 py-2">{formatDuration(activity.movingTime)}</td>
                    <td className="px-4 py-2">{activity.totalElevationGain}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="mt-4 flex justify-between items-center">
            <button
              onClick={goToPreviousPage}
              disabled={page === 0 || isLoading}
              className="px-4 py-2 bg-gray-200 text-sm rounded disabled:opacity-50"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-700">
              Page {page + 1} of {totalPages}
            </span>
            <button
              onClick={goToNextPage}
              disabled={page >= totalPages - 1 || isLoading}
              className="px-4 py-2 bg-gray-200 text-sm rounded disabled:opacity-50"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;