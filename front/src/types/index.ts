// Auth types
export interface AuthRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export interface CurrentUserResponse {
  id: string;
  username: string;
  is_superuser: boolean;
  roles: string[];
  email?: string | null;
}

export interface UserCreate {
  username: string;
  password: string;
  email?: string | null;
}

// Role types
export interface RoleResponse {
  id: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  users: UserBrief[];
}

export interface RoleListResponse {
  items: RoleResponse[];
  total: number;
  page: number;
  size: number;
}

export interface UpdateRoleRequest {
  name: string;
  description?: string | null;
}

export interface UserBrief {
  id: string;
  username: string;
}

export interface UserRoleAssignment {
  user_ids: string[];
}

// Social types
export type SocialProvider = 'vk' | 'yandex';

export interface SocialAccountResponse {
  provider: SocialProvider;
  social_id: string;
  social_username?: string | null;
  social_email?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  avatar_url?: string | null;
  is_primary: boolean;
  id: string;
  created_at: string;
  updated_at: string;
  token_expires_at?: string | null;
}

export interface SocialAccountList {
  accounts: SocialAccountResponse[];
}