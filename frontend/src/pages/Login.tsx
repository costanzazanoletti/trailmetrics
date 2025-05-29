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
    <div
      className="min-h-screen bg-cover bg-center relative flex items-center justify-center px-4"
      style={{
        backgroundImage: "url('/images/trail-bg.jpg')",
      }}
    >
      <div className="absolute inset-0 bg-[#5f3e2d]/50 backdrop-blur-sm"></div>

      <div className="relative z-10 bg-white/80 rounded-3xl shadow-lg px-8 py-12 max-w-sm w-full text-center">
        <div className="mb-6">
          <div className="text-4xl font-bold text-gray-600 tracking-tight">
            <span className="uppercase text-brand-sage">Trail</span>
            <span className="text-gray-600">Metrics</span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Explore. Run. Measure. Improve.
          </p>
        </div>

        {/* Slogan */}
        <p className="text-gray-600 text-sm mb-8 leading-snug">
          Login to unlock powerful insights and performance metrics from your
          trail runs.
        </p>

        {/* Pulsanti */}
        <div className="space-y-4">
          <button
            onClick={loginWithStrava}
            className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-lg text-base cursor-pointer transition"
          >
            <img
              src="/images/btn_strava_connect_with_orange_x2.png"
              alt="Connect with Strava"
            />
          </button>
        </div>

        {/* Footer o disclaimer */}
        <div className="text-xs text-gray-400 mt-6">
          By continuing, you agree to our{' '}
          <span className="underline">terms</span>.
        </div>
      </div>
    </div>
  );
};

export default Login;
