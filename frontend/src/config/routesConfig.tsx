import RequirePermission from '@/components/RequirePermission/RequirePermission';
import Chat from '@/pages/Chat';
import Layout from '@/pages/Layout';
import Authentication from '@/pages/Authentication';
import PageNotFound from '@/pages/PageNotFound';
import UserManagement from '@/pages/UserManagement';
import UsersList from '@/pages/UsersList';
import { RoutesType } from '@/types/types';
import ProtectedRoute from '@/routes/ProtectedRoutes';
import { routes as appRoutes } from '@/constants/routes';

const routes: RoutesType[] = [
  {
    path: appRoutes.home,
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: appRoutes.usersList,
        element: <UsersList />,
        primary: true,
      },
      {
        path: appRoutes.userManagement,
        element: (
          <RequirePermission permission="create:user">
            <UserManagement />
          </RequirePermission>
        ),
      },
      {
        path: appRoutes.chat,
        element: <Chat />,
      },
      {
        path: appRoutes.chatSession,
        element: <Chat />,
      },
    ],
  },
  {
    path: appRoutes.login,
    element: <Authentication />,
  },
  {
    path: appRoutes.pageNotFound,
    element: <PageNotFound />,
  },
];

export { routes };
