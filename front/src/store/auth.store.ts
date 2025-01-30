import { create } from 'zustand';
import { CurrentUserResponse } from '../types';
import { authService } from '../api/services';

interface AuthState {
  user: CurrentUserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (access_token: string, refresh_token: string) => Promise<void>;
  logout: () => Promise<void>;
  getCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (access_token: string, refresh_token: string) => {
    try {
      set({ isLoading: true, error: null });

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      const response = await authService.getCurrentUser(access_token);

      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: 'Failed to login',
        isLoading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  },

  logout: async () => {
    try {
      set({ isLoading: true, error: null });

      const access_token = localStorage.getItem('access_token') || '';
      const refresh_token = localStorage.getItem('refresh_token') || '';

      await authService.logout(access_token, refresh_token);

      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: 'Failed to logout',
        isLoading: false,
      });
      throw error;
    }
  },

  getCurrentUser: async () => {
    try {
      set({ isLoading: true, error: null });

      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await authService.getCurrentUser(token);

      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Failed to get current user',
      });
      throw error;
    }
  },
}));