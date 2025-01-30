import { apiClient } from './client';
import {
  AuthRequest,
  TokenResponse,
  CurrentUserResponse,
  UserCreate,
  RoleResponse,
  RoleListResponse,
  UpdateRoleRequest,
  UserRoleAssignment,
  SocialAccountList,
} from '../types';

// Auth Service
export const authService = {
  login: (data: AuthRequest) =>
    apiClient.post<TokenResponse>('/auth/login', data),

  register: (data: UserCreate) =>
    apiClient.post<TokenResponse>('/auth/register', data),

  logout: (access_token: string, refresh_token: string) =>
    apiClient.post('/auth/logout', null, { params: { access_token, refresh_token } }),

  getCurrentUser: (token: string) =>
    apiClient.get<CurrentUserResponse>('/auth/me', { params: { token } }),

  refreshToken: (refresh_token: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', null, { params: { refresh_token } }),
};

// Roles Service
export const rolesService = {
  getRoles: (page = 1, size = 10) =>
    apiClient.get<RoleListResponse>('/roles', { params: { page, size } }),

  getRole: (roleId: string) =>
    apiClient.get<RoleResponse>(`/roles/${roleId}`),

  createRole: (data: UpdateRoleRequest) =>
    apiClient.post<RoleResponse>('/roles', data),

  updateRole: (roleId: string, data: UpdateRoleRequest) =>
    apiClient.put<RoleResponse>(`/roles/${roleId}`, data),

  deleteRole: (roleId: string) =>
    apiClient.delete(`/roles/${roleId}`),

  assignUsersToRole: (roleId: string, data: UserRoleAssignment) =>
    apiClient.post(`/roles/${roleId}/users`, data),

  removeUsersFromRole: (roleId: string, data: UserRoleAssignment) =>
    apiClient.delete(`/roles/${roleId}/users`, { data }),

  getUsersByRole: (roleId: string) =>
    apiClient.get<UserRoleAssignment>(`/roles/${roleId}/users`),
};

// Social Auth Services
export const socialAuthService = {
  // VK
  vkLogin: () =>
    apiClient.get('/auth/vk/login'),

  vkAccounts: () =>
    apiClient.get<SocialAccountList>('/auth/vk/accounts'),

  // Yandex
  yandexLogin: () =>
    apiClient.get('/auth/yandex/login'),

  yandexAccounts: () =>
    apiClient.get<SocialAccountList>('/auth/yandex/accounts'),
};