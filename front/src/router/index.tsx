import { createBrowserRouter, Navigate, RouteObject } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { RolesPage } from '../pages/RolesPage';
import { ProfilePage } from '../pages/ProfilePage';
import { ProtectedRoute } from './ProtectedRoute';

const routes: RouteObject[] = [
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/profile" replace />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: 'profile',
        element: (
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'roles',
        element: (
          <ProtectedRoute>
            <RolesPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
];

export const router = createBrowserRouter(routes);