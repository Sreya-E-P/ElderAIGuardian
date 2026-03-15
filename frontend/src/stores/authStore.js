import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import api from '../services/api';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      initialize: async () => {
        const token = get().token || localStorage.getItem('token');
        if (token) {
          try {
            set({ isLoading: true });
            api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            const response = await api.get('/auth/me');
            set({ user: response.data, token, isLoading: false });
            localStorage.setItem('token', token);
          } catch (error) {
            console.error('Failed to fetch user:', error);
            set({ user: null, token: null, isLoading: false });
            localStorage.removeItem('token');
          }
        }
      },

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/login', { email, password });
          const data = response.data;

          // Backend returns access_token, not token
          const token = data.access_token || data.token;
          const user = data.user || data;

          // Set axios default header immediately
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

          // Save to localStorage for WebSocket
          localStorage.setItem('token', token);

          set({ user, token, isLoading: false, error: null });
          return { success: true };
        } catch (error) {
          const errMsg =
            error.response?.data?.detail ||
            error.response?.data?.message ||
            'Login failed';
          set({ error: errMsg, isLoading: false });
          return { success: false, error: errMsg };
        }
      },

      register: async (userData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/register', userData);
          const data = response.data;

          const token = data.access_token || data.token;
          const user = data.user || data;

          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          localStorage.setItem('token', token);

          set({ user, token, isLoading: false, error: null });
          return { success: true };
        } catch (error) {
          const errMsg =
            error.response?.data?.detail ||
            error.response?.data?.message ||
            'Registration failed';
          set({ error: errMsg, isLoading: false });
          return { success: false, error: errMsg };
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        delete api.defaults.headers.common['Authorization'];
        set({ user: null, token: null, error: null });
      },

      updateUser: (userData) => {
        set({ user: { ...get().user, ...userData } });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);