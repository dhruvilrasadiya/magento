import { useSessionStore } from '@/store/sessionStore';

export const useSession = () => {
  const loading = useSessionStore((state) => state.loading);
  const sessions = useSessionStore((state) => state.sessions);
  const hasMore = useSessionStore((state) => state.hasMore);
  const initialLoading = useSessionStore((state) => state.initialLoading);

  const setLoading = useSessionStore((state) => state.setLoading);
  const setSessions = useSessionStore((state) => state.setSessions);
  const addSessions = useSessionStore((state) => state.addSessions);
  const addSession = useSessionStore((state) => state.addSession);
  const removeSessionById = useSessionStore((state) => state.removeSessionById);
  const setHasMore = useSessionStore((state) => state.setHasMore);
  const setInitialLoading = useSessionStore((state) => state.setInitialLoading);
  const updateSession = useSessionStore((state) => state.updateSession);

  return {
    loading,
    sessions,
    setLoading,
    setSessions,
    addSessions,
    addSession,
    removeSessionById,
    hasMore,
    initialLoading,
    setHasMore,
    setInitialLoading,
    updateSession,
  };
};
