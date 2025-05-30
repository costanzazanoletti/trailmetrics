import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { fetchPlannedActivities } from '../services/activityService';
import {
  mapActivityFromApi,
  CamelCaseActivity,
} from '../mappers/activityMapper';
import { formatDuration } from '../utils/formatUtils';
import { ActivityStatusIcon } from '../components/ActivityStatusIcon';
import { PlusCircle } from 'lucide-react';

const Planning = () => {
  const [activities, setActivities] = useState<CamelCaseActivity[]>([]);
  const [searchParams] = useSearchParams();
  const initialPage = parseInt(searchParams.get('page') || '0', 10);
  const [page, setPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    fetchPlannedActivities(page, 10)
      .then((res) => {
        setActivities(res.content.map(mapActivityFromApi));
        setTotalPages(res.totalPages);
      })
      .catch((err) => console.error('Fetch error:', err))
      .finally(() => setIsLoading(false));
  }, [page]);

  const goToNextPage = () => {
    if (page < totalPages - 1) setPage((prev) => prev + 1);
  };

  const goToPreviousPage = () => {
    if (page > 0) setPage((prev) => prev - 1);
  };

  return (
    <div className="container mx-auto p-4 text-gray-600">
      <h1 className="text-2xl font-semibold mb-6">Planned Activities</h1>

      <div className="flex justify-end mb-4">
        <Link
          to="/planning/create"
          className="flex items-center gap-2 bg-brand-sage text-white px-4 py-2 rounded hover:bg-brand-sage-dark transition"
        >
          <PlusCircle className="w-5 h-5" />
          New Planned Activity
        </Link>
      </div>

      {isLoading ? (
        <p className="text-center text-sm text-gray-500 py-10">
          Loading planned activities...
        </p>
      ) : activities.length === 0 ? (
        <p>No planned activities found.</p>
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
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((activity) => (
                  <tr
                    key={activity.id}
                    className="border-t hover:bg-gray-50 text-sm"
                  >
                    <td className="px-4 py-2">{activity.sportType}</td>
                    <td className="px-4 py-2">
                      {new Date(activity.startDate).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2">{activity.name}</td>
                    <td className="px-4 py-2">
                      {(activity.distance / 1000).toFixed(2)}
                    </td>
                    <td className="px-4 py-2">
                      {formatDuration(activity.movingTime)}
                    </td>
                    <td className="px-4 py-2">{activity.totalElevationGain}</td>
                    <td className="px-4 py-2 text-center">
                      <ActivityStatusIcon status={activity.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

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

export default Planning;
