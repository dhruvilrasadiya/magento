import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { loginUser } from '@/services/api';
import { enqueueSnackbar } from 'notistack';
import { LoginApiPayload, UserType } from '@/types/types';

interface AuthState {
  user: UserType | null;
  isAuthenticated: boolean;
  login: (data: LoginApiPayload) => Promise<boolean>;
  logout: () => void;
  setUser: (user: UserType | null) => void;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      setUser: (user) => {
        set({
          user,
          isAuthenticated: !!user,
        });
      },
      setToken: (token) => {
        set((state) => ({
          user: state.user ? { ...state.user, token } : null,
        }));
      },

      login: async (data) => {
        try {
          const result = await loginUser(data);
          if (result.status !== 200) return false;

          const payload = {
            email: result.data.email,
            userName: result.data.user_name,
            userId: result.data.user_id,
            token: result.data.token,
            RefreshToken: result.data.refresh_token,
          };

          set({
            user: payload,
            isAuthenticated: true,
          });

          return true;
        } catch (error: any) {
          enqueueSnackbar(`${error.response?.data?.detail || 'Login Error!'}`, {
            variant: 'error',
          });
          return false;
        }
      },

      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
