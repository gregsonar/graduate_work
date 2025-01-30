import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '../store/auth.store';
import { authService } from '../api/services';

const schema = yup.object().shape({
  username: yup.string()
    .required('Username is required')
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters'),
  email: yup.string().email('Must be a valid email'),
  password: yup.string()
    .required('Password is required')
    .min(8, 'Password must be at least 8 characters'),
  confirmPassword: yup.string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('Please confirm your password'),
});

type RegisterFormData = yup.InferType<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: yupResolver(schema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setError(null);
      const { confirmPassword, ...registerData } = data;
      const response = await authService.register(registerData);
      await login(response.data.access_token, response.data.refresh_token);
      navigate('/profile', { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to register');
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        alignItems: 'flex-start',
        justifyContent: 'center',
        background: '#f0f2f5',
        paddingTop: '4rem',
        paddingBottom: '2rem',
        paddingInline: '1rem',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: '400px',
          padding: '2rem',
          borderRadius: '12px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          background: '#ffffff',
        }}
      >
        <CardHeader>
          <CardTitle
            style={{
              fontSize: '1.75rem',
              fontWeight: 'bold',
              color: '#333',
              textAlign: 'center',
              marginBottom: '1rem',
            }}
          >
            Create your account
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert
              style={{
                padding: '0.75rem',
                borderRadius: '8px',
                background: '#ffebee',
                color: '#c62828',
                border: '1px solid #ffcdd2',
                marginBottom: '1rem',
              }}
            >
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleSubmit(onSubmit)} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <Input
                {...register('username')}
                type="text"
                placeholder="Username"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: errors.username ? '1px solid #e74c3c' : '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  transition: 'border-color 0.3s ease',
                }}
              />
              {errors.username && (
                <p
                  style={{
                    marginTop: '0.25rem',
                    fontSize: '0.875rem',
                    color: '#e74c3c',
                  }}
                >
                  {errors.username.message}
                </p>
              )}
            </div>
            <div>
              <Input
                {...register('email')}
                type="email"
                placeholder="Email (optional)"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: errors.email ? '1px solid #e74c3c' : '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  transition: 'border-color 0.3s ease',
                }}
              />
              {errors.email && (
                <p
                  style={{
                    marginTop: '0.25rem',
                    fontSize: '0.875rem',
                    color: '#e74c3c',
                  }}
                >
                  {errors.email.message}
                </p>
              )}
            </div>
            <div>
              <Input
                {...register('password')}
                type="password"
                placeholder="Password"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: errors.password ? '1px solid #e74c3c' : '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  transition: 'border-color 0.3s ease',
                }}
              />
              {errors.password && (
                <p
                  style={{
                    marginTop: '0.25rem',
                    fontSize: '0.875rem',
                    color: '#e74c3c',
                  }}
                >
                  {errors.password.message}
                </p>
              )}
            </div>
            <div>
              <Input
                {...register('confirmPassword')}
                type="password"
                placeholder="Confirm password"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: errors.confirmPassword ? '1px solid #e74c3c' : '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  transition: 'border-color 0.3s ease',
                }}
              />
              {errors.confirmPassword && (
                <p
                  style={{
                    marginTop: '0.25rem',
                    fontSize: '0.875rem',
                    color: '#e74c3c',
                  }}
                >
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <Button
                type="submit"
                disabled={isSubmitting}
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
                {isSubmitting ? 'Creating account...' : 'Create account'}
              </Button>
              <p
                style={{
                  fontSize: '0.9rem',
                  color: '#555',
                  textAlign: 'center',
                }}
              >
                Already have an account?{' '}
                <Link
                  to="/login"
                  style={{
                    color: '#007bff',
                    textDecoration: 'none',
                    fontWeight: 'bold',
                    transition: 'color 0.3s ease',
                  }}
                >
                  Sign in here
                </Link>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}