import { useEffect} from 'react';
import { fetchActivities } from '../services/activityService';

const Dashboard = () => {
  useEffect(() => {
    fetchActivities()
      .then((data) => {
        console.log("Fetched activities:", data);
      })
      .catch((error) => {
        console.error("Error fetching activities:", error);
      });
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p>Check the console for fetched activities.</p>
    </div>
  );
};

export default Dashboard;