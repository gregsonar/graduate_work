import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function ProtectedRoute() {
  const { tokens } = useAuthStore();
  
  if (!tokens) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}