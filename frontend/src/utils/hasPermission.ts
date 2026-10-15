import { permissions } from '@/constants/roles';
import { Permissions, Role } from '@/types/types';

export const hasPermission = (role: Role, permission: Permissions): boolean => {
  return permissions[role]?.includes(permission) ?? false;
};
