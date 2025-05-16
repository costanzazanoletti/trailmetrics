import { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';

export function Navbar() {
  const { user, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const [imageError, setImageError] = useState(false);

  if (!user) return null;

  const profileImg =
    !imageError && user.profileUrl
      ? user.profileUrl
      : '/images/placeholder-avatar.png';

  return (
    <nav className="flex items-center justify-between px-6 py-4 bg-white shadow-md">
      <div className="text-4xl font-bold text-gray-600 tracking-tight">
        <span className="uppercase text-brand-sage">Trail</span>
        <span className="text-gray-600">Metrics</span>
      </div>
      <div className="relative">
        <img
          src={profileImg}
          alt="User Avatar"
          className="w-10 h-10 rounded-full cursor-pointer"
          onClick={() => setMenuOpen(!menuOpen)}
          onError={() => setImageError(true)}
        />
        {menuOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-white border rounded-md shadow-lg z-50">
            <div className="px-4 py-2 text-sm text-gray-700 border-b">
              {user.firstname} {user.lastname}
            </div>
            <button
              onClick={() => {
                logout();
                setMenuOpen(false);
              }}
              className="w-full text-left px-4 py-2 text-sm text-orange-600 hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
