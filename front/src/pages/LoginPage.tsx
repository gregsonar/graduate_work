import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuthStore } from '../store/auth.store';
import { authService } from '../api/services';

const schema = yup.object().shape({
  username: yup.string().required('Username is required').min(3, 'Username must be at least 3 characters'),
  password: yup.string().required('Password is required'),
});

type LoginFormData = yup.InferType<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: yupResolver(schema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setError(null);
      const response = await authService.login(data);
      await login(response.data.access_token, response.data.refresh_token);
      navigate('/profile', { replace: true });
    } catch (err) {
      setError('Invalid username or password');
    }
  };

  return (
    <div
      style={{
        maxWidth: '400px',
        margin: '0 auto',
        padding: '2rem',
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.06)',
        textAlign: 'center',
      }}
    >
      <h1
        style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          color: '#333',
          marginBottom: '1.5rem',
        }}
      >
        Sign In
      </h1>
      {error && (
        <div
          style={{
            color: '#e74c3c',
            fontSize: '0.875rem',
            marginBottom: '1rem',
          }}
        >
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit(onSubmit)} style={{ textAlign: 'left' }}>
        <div
          style={{
            marginBottom: '1rem',
          }}
        >
          <label
            style={{
              display: 'block',
              fontSize: '0.9rem',
              color: '#555',
              marginBottom: '0.5rem',
            }}
          >
            Username
          </label>
          <input
            {...register('username')}
            type="text"
            placeholder="Enter your username"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '1rem',
              transition: 'border-color 0.3s ease',
            }}
          />
          {errors.username && (
            <div
              style={{
                color: '#e74c3c',
                fontSize: '0.875rem',
                marginTop: '0.25rem',
              }}
            >
              {errors.username.message}
            </div>
          )}
        </div>
        <div
          style={{
            marginBottom: '1rem',
          }}
        >
          <label
            style={{
              display: 'block',
              fontSize: '0.9rem',
              color: '#555',
              marginBottom: '0.5rem',
            }}
          >
            Password
          </label>
          <input
            {...register('password')}
            type="password"
            placeholder="Enter your password"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '1rem',
              transition: 'border-color 0.3s ease',
            }}
          />
          {errors.password && (
            <div
              style={{
                color: '#e74c3c',
                fontSize: '0.875rem',
                marginTop: '0.25rem',
              }}
            >
              {errors.password.message}
            </div>
          )}
        </div>
        <button
          type="submit"
          style={{
            width: '100%',
            padding: '0.75rem',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            cursor: 'pointer',
            transition: 'background 0.3s ease',
            marginBottom: '1rem',
          }}
          disabled={isSubmitting}
        >
          Sign In
        </button>
        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
            justifyContent: 'space-between',
            marginBottom: '1rem',
          }}
        >
          <Link
            to="/auth/vk/login"
            style={{
              flex: 1,
              padding: '0.75rem',
              background: '#fff',
              color: '#007bff',
              border: '1px solid #007bff',
              borderRadius: '8px',
              fontSize: '0.9rem',
              textDecoration: 'none',
              textAlign: 'center',
              transition: 'background 0.3s ease, color 0.3s ease',
            }}
          >
            Sign in with VK
          </Link>
          <Link
            to="/auth/yandex/login"
            style={{
              flex: 1,
              padding: '0.75rem',
              background: '#fff',
              color: '#007bff',
              border: '1px solid #007bff',
              borderRadius: '8px',
              fontSize: '0.9rem',
              textDecoration: 'none',
              textAlign: 'center',
              transition: 'background 0.3s ease, color 0.3s ease',
            }}
          >
            Sign in with Yandex
          </Link>
        </div>
        <div
          style={{
            fontSize: '0.9rem',
            color: '#555',
            textAlign: 'center',
          }}
        >
          Don't have an account?{' '}
          <Link
            to="/register"
            style={{
              color: '#007bff',
              textDecoration: 'none',
              transition: 'color 0.3s ease',
            }}
          >
            Sign up
          </Link>
        </div>
      </form>
    </div>
  );
}