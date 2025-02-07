import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { CurrentUserResponse, TokenResponse } from '../types/auth';

interface AuthState {
  user: CurrentUserResponse | null;
  tokens: TokenResponse | null;
  setUser: (user: CurrentUserResponse | null) => void;
  setTokens: (tokens: TokenResponse | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      setUser: (user) => set({ user }),
      setTokens: (tokens) => set({ tokens }),
      logout: () => set({ user: null, tokens: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);