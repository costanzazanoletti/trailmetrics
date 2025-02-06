import { create } from 'zustand';

type UserState = {
  user: any;
  setUser: (userData: any) => void;
  logout: () => void;
};

export const useUserStore = create<UserState>((set) => ({
  user: null,
  setUser: (userData) => set({ user: userData }),
  logout: () => set({ user: null }),
}));
