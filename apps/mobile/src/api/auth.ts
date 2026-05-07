import { api } from './client';
import { Family, User } from '../auth/store';

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface MeResponse {
  id: string;
  name: string;
  profile_image: string | null;
  families: Family[];
}

export type MockUserCode = 'mock-user-1' | 'mock-user-2' | 'mock-user-3';

/**
 * Real Kakao OAuth login — sends authCode + redirectUri to backend.
 * W2에서 실 카카오 OAuth 연동 시 사용.
 */
export async function loginWithKakao(
  authCode: string,
  redirectUri: string,
): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>('/auth/kakao', {
    auth_code: authCode,
    redirect_uri: redirectUri,
  });
  return res.data;
}

/**
 * 개발 전용 mock 로그인 — mock-user-1/2/3 코드를 auth_code 로 전달.
 */
export async function loginWithMock(mockUser: MockUserCode): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>('/auth/kakao', {
    auth_code: mockUser,
    redirect_uri: 'http://localhost',
  });
  return res.data;
}

/**
 * refresh 토큰으로 새 access + refresh 발급.
 */
export async function refreshTokens(refresh: string): Promise<{ access: string; refresh: string }> {
  const res = await api.post<{ access: string; refresh: string }>('/auth/refresh', { refresh });
  return res.data;
}

/**
 * 로그아웃 — 서버 refresh 토큰 폐기.
 */
export async function logout(refresh: string): Promise<void> {
  await api.post('/auth/logout', { refresh });
}

/**
 * 현재 로그인 사용자 정보 + 가족 목록 조회.
 */
export async function me(): Promise<MeResponse> {
  const res = await api.get<MeResponse>('/me');
  return res.data;
}
