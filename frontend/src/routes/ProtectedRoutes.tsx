import { JSX } from '@emotion/react/jsx-runtime';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { routes } from '@/constants/routes';

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated || !user) {
    return <Navigate to={routes.login} replace />;
  }

  return children;
}
