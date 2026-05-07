// expo-camera 권한 요청 헬퍼.

import { Camera } from 'expo-camera';

export type PermissionResult =
  | { ok: true }
  | { ok: false; reason: 'denied' | 'error'; message?: string };

export async function ensureCameraPermission(): Promise<PermissionResult> {
  try {
    const { status } = await Camera.requestCameraPermissionsAsync();
    return status === 'granted' ? { ok: true } : { ok: false, reason: 'denied' };
  } catch (e) {
    return {
      ok: false,
      reason: 'error',
      message: e instanceof Error ? e.message : 'unknown error',
    };
  }
}
