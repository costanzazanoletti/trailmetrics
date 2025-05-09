import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { syncActivities } from '../services/activityService';

export function AppLayout() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const hasSynced = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated || hasSynced.current) return;
    syncActivities()
      .then(() => {
        hasSynced.current = true;
      })
      .catch((err) => {
        console.error('Error during activities sync:', err);
        if (err?.response?.status === 401) {
          useAuthStore.getState().logout(); // logout
          navigate('/', { replace: true }); // go to the login page
          navigate('/login', { replace: true });
        }
      });
  }, [isAuthenticated]);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Top Navbar */}
      <Navbar />

      {/* Horizontal menu with sections */}
      <div className="flex gap-6 px-6 py-4 bg-white shadow-sm border-b">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `text-sm font-medium ${
              isActive ? 'text-blue-600' : 'text-gray-600'
            } hover:underline`
          }
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/planning"
          className={({ isActive }) =>
            `text-sm font-medium ${
              isActive ? 'text-blue-600' : 'text-gray-600'
            } hover:underline`
          }
        >
          Planning
        </NavLink>
      </div>

      {/* Dynamic content */}
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
