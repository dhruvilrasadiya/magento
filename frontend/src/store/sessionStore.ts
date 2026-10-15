import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { SessionType } from '@/types/types';

type SessionStore = {
  sessions: SessionType[];
  loading: boolean;
  initialLoading: boolean;
  hasMore: boolean;
  addSessions: (sessions: SessionType[]) => void;
  addSession: (session: SessionType) => void;
  setSessions: (sessions: SessionType[]) => void;
  removeSessionById: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setInitialLoading: (val: boolean) => void;
  setHasMore: (val: boolean) => void;
  updateSession: (sessionId: string, updates: Partial<SessionType>) => void;
};

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      sessions: [],
      loading: false,
      initialLoading: true,
      hasMore: true,
      addSessions: (sessions) => set((state) => ({ sessions: [...state.sessions, ...sessions] })),
      addSession: (session) => set((state) => ({ sessions: [session, ...state.sessions] })),
      setSessions: (sessions) => set({ sessions }),
      removeSessionById: (id) =>
        set((state) => ({
          sessions: state.sessions.filter((s) => s.session_id !== id),
        })),
      setLoading: (val) => set({ loading: val }),
      setInitialLoading: (val) => set({ initialLoading: val }),
      setHasMore: (val) => set({ hasMore: val }),
      updateSession: (sessionId, updates) =>
        set((state) => ({
          sessions: state.sessions.map((session) =>
            session.session_id === sessionId ? { ...session, ...updates } : session
          ),
        })),
    }),
    { name: 'sessions' }
  )
);
