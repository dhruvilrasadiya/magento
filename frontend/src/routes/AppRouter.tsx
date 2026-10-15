import { Routes as RouterRoutes, Route } from 'react-router-dom';
import { routes } from '@/config/routesConfig';

function AppRouter() {
  return (
    <RouterRoutes>
      {routes.map(({ path, element, children }) => (
        <Route key={`parent-${path}`} path={path} element={element}>
          {children?.map(({ path: childPath, element: childElement, primary }) => (
            <Route
              key={`child-${childPath}`}
              path={primary ? undefined : childPath}
              index={primary || childPath === '' || childPath === undefined}
              element={childElement}
            />
          ))}
        </Route>
      ))}
    </RouterRoutes>
  );
}

export default AppRouter;
