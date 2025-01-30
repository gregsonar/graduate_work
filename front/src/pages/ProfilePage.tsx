import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '../store/auth.store';
import { authService, socialAuthService } from '../api/services';

interface PasswordChangeData {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export function ProfilePage() {
  const { user } = useAuthStore();
  const [passwordData, setPasswordData] = useState<PasswordChangeData>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Получение связанных социальных аккаунтов
  const { data: vkAccounts } = useQuery({
    queryKey: ['vk-accounts'],
    queryFn: () => socialAuthService.vkAccounts(),
    select: (response) => response.data,
  });

  const { data: yandexAccounts } = useQuery({
    queryKey: ['yandex-accounts'],
    queryFn: () => socialAuthService.yandexAccounts(),
    select: (response) => response.data,
  });

  // Мутация для изменения пароля
  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: () => {
      setSuccess('Password successfully changed');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      setError(null);
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to change password');
      setSuccess(null);
    },
  });

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      return;
    }
    changePasswordMutation.mutate({
      current_password: passwordData.current_password,
      new_password: passwordData.new_password,
    });
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      {/* Основная информация */}
      <Card style={{ marginBottom: '1.5rem', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        <CardHeader>
          <CardTitle style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>Profile Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.9rem', color: '#555', fontWeight: 'bold' }}>Username</label>
              <div style={{ marginTop: '0.5rem', fontSize: '1.1rem', color: '#333' }}>{user?.username}</div>
            </div>
            <div>
              <label style={{ fontSize: '0.9rem', color: '#555', fontWeight: 'bold' }}>Email</label>
              <div style={{ marginTop: '0.5rem', fontSize: '1.1rem', color: '#333' }}>{user?.email || 'Not set'}</div>
            </div>
            <div>
              <label style={{ fontSize: '0.9rem', color: '#555', fontWeight: 'bold' }}>Roles</label>
              <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {user?.roles.map((role) => (
                  <span
                    key={role}
                    style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '16px',
                      fontSize: '0.8rem',
                      backgroundColor: '#e1effe',
                      color: '#1a73e8',
                      fontWeight: 'bold',
                    }}
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Изменение пароля */}
      <Card style={{ marginBottom: '1.5rem', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        <CardHeader>
          <CardTitle style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>Change Password</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {error && (
              <Alert style={{ padding: '0.75rem', borderRadius: '8px', background: '#ffebee', color: '#c62828', border: '1px solid #ffcdd2' }}>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {success && (
              <Alert style={{ padding: '0.75rem', borderRadius: '8px', background: '#e8f5e9', color: '#2e7d32', border: '1px solid #c8e6c9' }}>
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}
            <Input
              type="password"
              value={passwordData.current_password}
              onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
              placeholder="Current password"
              style={{
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1rem',
                transition: 'border-color 0.3s ease',
              }}
            />
            <Input
              type="password"
              value={passwordData.new_password}
              onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
              placeholder="New password"
              style={{
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1rem',
                transition: 'border-color 0.3s ease',
              }}
            />
            <Input
              type="password"
              value={passwordData.confirm_password}
              onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
              placeholder="Confirm new password"
              style={{
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1rem',
                transition: 'border-color 0.3s ease',
              }}
            />
            <Button
              type="submit"
              disabled={changePasswordMutation.isPending}
              style={{
                padding: '0.75rem',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'background 0.3s ease',
              }}
            >
              {changePasswordMutation.isPending ? 'Changing...' : 'Change Password'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Социальные аккаунты */}
      <Card style={{ padding: '1.5rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        <CardHeader>
          <CardTitle style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>Linked Social Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* VK аккаунты */}
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem', color: '#333' }}>VK Accounts</h3>
              {vkAccounts?.accounts.length ? (
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {vkAccounts.accounts.map((account) => (
                    <li key={account.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <p style={{ fontSize: '1rem', fontWeight: 'bold', color: '#333' }}>{account.social_username || 'No username'}</p>
                        <p style={{ fontSize: '0.9rem', color: '#555' }}>{account.social_email}</p>
                      </div>
                      <Button
                        asChild
                        variant="outline"
                        style={{
                          padding: '0.5rem 1rem',
                          border: '1px solid #007bff',
                          background: 'transparent',
                          color: '#007bff',
                          borderRadius: '8px',
                          fontSize: '0.9rem',
                          cursor: 'pointer',
                          transition: 'background 0.3s ease, color 0.3s ease',
                        }}
                      >
                        <a href={`/api/v1/auth/vk/unlink/${account.social_id}`}>Unlink Account</a>
                      </Button>
                    </li>
                  ))}
                </ul>
              ) : (
                <Button
                  asChild
                  style={{
                    padding: '0.75rem',
                    background: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    cursor: 'pointer',
                    transition: 'background 0.3s ease',
                  }}
                >
                  <a href="/api/v1/auth/vk/login">Link VK Account</a>
                </Button>
              )}
            </div>

            {/* Yandex аккаунты */}
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem', color: '#333' }}>Yandex Accounts</h3>
              {yandexAccounts?.accounts.length ? (
                <ul style={{ listStyle: 'none', padding: '0', margin: '0', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {yandexAccounts.accounts.map((account) => (
                    <li key={account.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <p style={{ fontSize: '1rem', fontWeight: 'bold', color: '#333' }}>{account.social_username || 'No username'}</p>
                        <p style={{ fontSize: '0.9rem', color: '#555' }}>{account.social_email}</p>
                      </div>
                      <Button
                        asChild
                        variant="outline"
                        style={{
                          padding: '0.5rem 1rem',
                          border: '1px solid #007bff',
                          background: 'transparent',
                          color: '#007bff',
                          borderRadius: '8px',
                          fontSize: '0.9rem',
                          cursor: 'pointer',
                          transition: 'background 0.3s ease, color 0.3s ease',
                        }}
                      >
                        <a href={`/api/v1/auth/yandex/unlink/${account.social_id}`}>Unlink Account</a>
                      </Button>
                    </li>
                  ))}
                </ul>
              ) : (
                <Button
                  asChild
                  style={{
                    padding: '0.75rem',
                    background: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    cursor: 'pointer',
                    transition: 'background 0.3s ease',
                  }}
                >
                  <a href="/api/v1/auth/yandex/login">Link Yandex Account</a>
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}