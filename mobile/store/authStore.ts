import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../services/api';
import { getApiErrorMessage } from '../services/errors';
import { User, LoginCredentials, RegisterData } from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  updateAvatarUrl: (avatarUrl: string | null) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const { access_token } = await authAPI.login(credentials);
      await SecureStore.setItemAsync('access_token', access_token);

      const user = await authAPI.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      const errorMessage = getApiErrorMessage(error, 'Login failed');
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await authAPI.register(data);
      // Auto-login after registration
      await get().login({
        email: data.email,
        password: data.password,
      });
    } catch (error: any) {
      const errorMessage = getApiErrorMessage(error, 'Registration failed');
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('access_token');
    set({ user: null, isAuthenticated: false, error: null });
  },

  loadUser: async () => {
    set({ isLoading: true });
    try {
      const token = await SecureStore.getItemAsync('access_token');
      if (!token) {
        set({ isLoading: false });
        return;
      }

      const user = await authAPI.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      await SecureStore.deleteItemAsync('access_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  updateAvatarUrl: async (avatarUrl) => {
    const user = await authAPI.updateProfile({ avatar_url: avatarUrl });
    set({ user });
  },

  clearError: () => set({ error: null }),
}));
