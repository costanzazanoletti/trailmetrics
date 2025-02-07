import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { loginWithStrava } from '../services/authService'; // Use centralized API call

const Login = () => {
  const navigate = useNavigate();
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]); // Calls only once when component mounts

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      {!isAuthenticated ? (
        <button
          className="bg-orange-500 text-white px-6 py-3 rounded-md text-lg"
          onClick={loginWithStrava}
        >
          Connect with Strava
        </button>
      ) : null}
    </div>
  );
};

export default Login;
