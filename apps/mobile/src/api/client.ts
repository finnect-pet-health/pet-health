import axios from 'axios';
import { useAuthStore } from '../auth/store';

const BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${BASE_URL}/v1`,
  timeout: 10_000,
});

// ─── Request interceptor: attach access token ───────────────────────────────
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── 401 refresh-and-retry logic ────────────────────────────────────────────
let refreshPromise: Promise<void> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    const axiosError = error as {
      config?: { _retried?: boolean; headers?: Record<string, string> };
      response?: { status?: number };
    };

    const status = axiosError.response?.status;
    const originalRequest = axiosError.config;

    if (status !== 401 || !originalRequest || originalRequest._retried) {
      return Promise.reject(error);
    }

    originalRequest._retried = true;

    // Coalesce concurrent 401s into a single refresh attempt
    if (!refreshPromise) {
      refreshPromise = (async () => {
        const { refreshToken, setSession, clear } = useAuthStore.getState();

        if (!refreshToken) {
          clear();
          throw new Error('No refresh token available');
        }

        let refreshData: { access: string; refresh: string };
        try {
          const res = await axios.post<{ access: string; refresh: string }>(
            `${BASE_URL}/v1/auth/refresh`,
            { refresh: refreshToken },
          );
          refreshData = res.data;
        } catch {
          clear();
          throw new Error('Token refresh failed');
        }

        // Preserve existing user — only tokens are replaced
        const { user } = useAuthStore.getState();
        if (!user) {
          clear();
          throw new Error('No user in store after refresh');
        }

        setSession({
          access: refreshData.access,
          refresh: refreshData.refresh,
          user,
        });
      })();

      // Always clear the shared promise when done (success or failure)
      refreshPromise = refreshPromise.finally(() => {
        refreshPromise = null;
      });
    }

    try {
      await refreshPromise;
    } catch {
      return Promise.reject(error);
    }

    // Retry original request with updated token
    const newToken = useAuthStore.getState().accessToken;
    if (newToken && originalRequest.headers) {
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
    }

    return api(axiosError.config as Parameters<typeof api>[0]);
  },
);
