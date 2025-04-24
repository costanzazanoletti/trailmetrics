import { create } from 'zustand';
import { persist, PersistStorage } from 'zustand/middleware';
import { checkAuth, logout } from '../services/authService'; // Use centralized API function
// Custom localStorage wrapper for Zustand
const zustandStorage: PersistStorage<AuthState> = {
  getItem: (name) => {
    const storedValue = localStorage.getItem(name);
    return storedValue ? JSON.parse(storedValue) : null;
  },
  setItem: (name, value) => {
    localStorage.setItem(name, JSON.stringify(value));
  },
  removeItem: (name) => {
    localStorage.removeItem(name);
  },
};

interface User {
  firstname: string;
  lastname: string;
  profileUrl: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create(
  persist<AuthState>(
    (set, get) => ({
      user: null,
      isAuthenticated: false,

      setUser: (user) => set({ user, isAuthenticated: true }),

      logout: async () => {
        await logout();
        set({ user: null, isAuthenticated: false });
      },

      checkAuth: async () => {
        if (get().isAuthenticated) return;

        const data = await checkAuth();
        if (data.authenticated) {
          set({
            user: {
              firstname: data.firstname || '',
              lastname: data.lastname || '',
              profileUrl: data.profileUrl || '',
            },
            isAuthenticated: true,
          });
        } else {
          set({ isAuthenticated: false });
        }
      },
    }),
    {
      name: 'auth-storage', // Persist authentication state
      storage: zustandStorage,
    }
  )
);
