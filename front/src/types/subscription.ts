export type SubscriptionPlanType = 'basic' | 'standard' | 'premium';
export type SubscriptionStatus = 'active' | 'pending' | 'canceled' | 'expired' | 'suspended';

export interface SubscriptionResponse {
  plan_type: SubscriptionPlanType;
  start_date: string;
  end_date: string;
  price: string;
  is_auto_renewable: boolean;
  id: string;
  user_id: string;
  status: SubscriptionStatus;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionHistoryResponse {
  id: string;
  subscription_id: string;
  action: string;
  details?: Record<string, any>;
  created_at: string;
}