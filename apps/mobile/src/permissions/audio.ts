// expo-av 오디오 녹음 권한 요청 헬퍼.

import { Audio } from 'expo-av';

export type PermissionResult =
  | { ok: true }
  | { ok: false; reason: 'denied' | 'error'; message?: string };

export async function ensureAudioPermission(): Promise<PermissionResult> {
  try {
    const { status } = await Audio.requestPermissionsAsync();
    return status === 'granted' ? { ok: true } : { ok: false, reason: 'denied' };
  } catch (e) {
    return {
      ok: false,
      reason: 'error',
      message: e instanceof Error ? e.message : 'unknown error',
    };
  }
}
