import { Permissions, Role } from '@/types/types';

export const permissions: Record<Role, Permissions[]> = {
  superadmin: [
    'create:admin',
    'create:user',
    'edit:admin',
    'delete:admin',

    'create:supervisor',
    'create:user',
    'edit:supervisor',
    'delete:supervisor',

    'view',
    'edit:all',
    'delete:all',
  ],
  admin: [
    'create:supervisor',
    'create:user',
    'edit:supervisor',
    'delete:supervisor',
    'view',
    'edit:all',
    'delete:all',
  ],
  supervisor: ['view'],
} as const;
