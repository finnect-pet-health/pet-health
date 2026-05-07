import * as SecureStore from 'expo-secure-store';
import { create } from 'zustand';

const SECURE_STORE_KEY = 'petfinect_session';

export interface User {
  id: string;
  name: string;
  profile_image: string | null;
}

export interface Family {
  id: string;
  name: string;
  role: 'owner' | 'member';
  member_count?: number;
}

interface Session {
  access: string;
  refresh: string;
  user: User;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  families: Family[];
  hydrated: boolean;
}

interface AuthActions {
  setSession: (session: Session) => void;
  setFamilies: (families: Family[]) => void;
  clear: () => void;
  hydrate: () => Promise<void>;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  families: [],
  hydrated: false,

  setSession: (session) => {
    const { access, refresh, user } = session;
    // Persist to SecureStore (fire-and-forget; errors are non-fatal in normal flow)
    const payload = JSON.stringify({ access, refresh, user });
    SecureStore.setItemAsync(SECURE_STORE_KEY, payload).catch(() => {});
    set({ accessToken: access, refreshToken: refresh, user });
  },

  setFamilies: (families) => {
    set({ families });
  },

  clear: () => {
    SecureStore.deleteItemAsync(SECURE_STORE_KEY).catch(() => {});
    set({ accessToken: null, refreshToken: null, user: null, families: [] });
  },

  hydrate: async () => {
    try {
      const raw = await SecureStore.getItemAsync(SECURE_STORE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          access: string;
          refresh: string;
          user: User;
        };
        set({
          accessToken: parsed.access,
          refreshToken: parsed.refresh,
          user: parsed.user,
        });
      }
    } catch {
      // Corrupted data — wipe it
      await SecureStore.deleteItemAsync(SECURE_STORE_KEY).catch(() => {});
    } finally {
      set({ hydrated: true });
    }
  },
}));
