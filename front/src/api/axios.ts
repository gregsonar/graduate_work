import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: 'http://localhost',
  withCredentials: true
});

api.interceptors.request.use((config) => {
  const tokens = useAuthStore.getState().tokens;
  if (tokens) {
    config.headers.Authorization = `Bearer ${tokens.access_token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const tokens = useAuthStore.getState().tokens;
        if (tokens) {
          const response = await axios.post('http://localhost/api/v1/auth/refresh', {}, {
            headers: { Authorization: `Bearer ${tokens.refresh_token}` }
          });
          useAuthStore.getState().setTokens(response.data);
          return api(originalRequest);
        }
      } catch (error) {
        useAuthStore.getState().logout();
      }
    }
    return Promise.reject(error);
  }
);

export default api;