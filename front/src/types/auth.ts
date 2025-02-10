export interface AuthRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

export interface CurrentUserResponse {
  id: string;
  username: string;
  is_superuser: boolean;
  roles: string[];
  email?: string;
}

export interface SocialAccountResponse {
  provider: 'vk' | 'yandex';
  social_id: string;
  social_username?: string;
  social_email?: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  is_primary: boolean;
  id: string;
  created_at: string;
  updated_at: string;
  token_expires_at?: string;
}