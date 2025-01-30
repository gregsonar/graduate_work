import { useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '../store/auth.store';

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout, getCurrentUser } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated && !['/login', '/register'].includes(location.pathname)) {
      getCurrentUser().catch(() => {
        navigate('/login');
      });
    }
  }, [isAuthenticated, getCurrentUser, navigate, location]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Не показываем навигацию на страницах входа и регистрации
  const hideNavigation = ['/login', '/register'].includes(location.pathname);

  if (hideNavigation) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Навигационная панель */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <Link to="/profile" className="text-gray-900 font-medium">
                Profile
              </Link>
              {user?.is_superuser && (
                <Link to="/roles" className="text-gray-900 font-medium">
                  Roles
                </Link>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {user && (
                <span className="text-gray-600">
                  Welcome, {user.username}
                </span>
              )}
              <Button onClick={handleLogout} variant="outline">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Основной контент */}
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>

      {/* Футер */}
      <footer className="bg-white border-t mt-auto">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-gray-600">
            © {new Date().getFullYear()} Your Company Name
          </div>
        </div>
      </footer>
    </div>
  );
}