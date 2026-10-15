import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Permissions, UserTokenPayload } from '@/types/types';
import { hasPermission } from '@/utils/hasPermission';
import { jwtDecode } from 'jwt-decode';
import { memo } from 'react';
import { routes } from '@/constants/routes';

type Props = {
  permission: Permissions;
  children: React.ReactNode;
  condition?: () => boolean;
};

const RequirePermission = ({ permission, children, condition }: Props) => {
  const { user, logout } = useAuth();

  if (!user?.token) {
    logout();
    return <Navigate to={routes.login} replace />;
  }

  let jwtPayload: UserTokenPayload;
  try {
    jwtPayload = jwtDecode<UserTokenPayload>(user.token);
  } catch (error) {
    logout();
    console.error('Failed to decode JWT token:', error);
    return <Navigate to={routes.login} replace />;
  }

  const hasRequiredPermission = hasPermission(jwtPayload.role, permission);
  const passesCondition = condition ? condition() : true;

  if (!hasRequiredPermission || !passesCondition) {
    return null;
  }

  return <>{children}</>;
};

export default memo(RequirePermission);
