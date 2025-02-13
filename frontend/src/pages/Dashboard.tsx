import { useEffect } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { fetchActivities } from '../services/activityService';

const Dashboard = () => {
  const { user, isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      checkAuth();
    } else {
      fetchActivities()
        .then((data) => console.log(data))
        .catch((error) => console.log(error));
    }
  }, [isAuthenticated, checkAuth]);

  if (!isAuthenticated) {
    window.location.href = '/';
    return null;
  }

  return (
    <div className="container mx-auto p-4">
      <h1>
        Welcome, {user?.firstname} {user?.lastname}
      </h1>
      <button
        onClick={() => useAuthStore.getState().logout()}
        className="bg-red-500 text-white px-4 py-2 rounded-md"
      >
        Logout
      </button>
    </div>
  );
};

export default Dashboard;
