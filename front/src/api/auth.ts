import api from './axios';
import { AuthRequest, CurrentUserResponse, SocialAccountResponse, TokenResponse } from '../types/auth';

export const authApi = {
  login: (data: AuthRequest) => 
    api.post<TokenResponse>('/api/v1/auth/login', data),
  
  register: (data: AuthRequest) =>
    api.post<TokenResponse>('/api/v1/auth/register', data),
    
  getCurrentUser: () =>
    api.get<CurrentUserResponse>('/api/v1/auth/me'),
    
  logout: () =>
    api.post('/api/v1/auth/logout'),
    
  getVkLoginUrl: () =>
    api.get<{ auth_url: string }>('/api/v1/auth/vk/login'),
    
  getYandexLoginUrl: () =>
    api.get<{ auth_url: string }>('/api/v1/auth/yandex/login'),
    
  getSocialAccounts: () =>
    api.get<{ accounts: SocialAccountResponse[] }>('/api/v1/auth/vk/accounts'),
};