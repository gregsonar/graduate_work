import api from './axios';
import { SubscriptionResponse, SubscriptionHistoryResponse } from '../types/subscription';

export const subscriptionApi = {
  getCurrentSubscription: () =>
    api.get<SubscriptionResponse>('/api/v1/subscription/current'),
    
  getSubscriptionHistory: (subscriptionId: string) =>
    api.get<SubscriptionHistoryResponse[]>(`/api/v1/subscription/${subscriptionId}/history`),
    
  suspendSubscription: (subscriptionId: string, reason: string) =>
    api.post(`/api/v1/subscription/${subscriptionId}/suspend`, { reason }),
    
  resumeSubscription: (subscriptionId: string) =>
    api.post(`/api/v1/subscription/${subscriptionId}/resume`, {}),
    
  cancelSubscription: (subscriptionId: string, reason: string) =>
    api.post(`/api/v1/subscription/${subscriptionId}/cancel`, { reason }),
};