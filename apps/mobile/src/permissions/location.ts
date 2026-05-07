// expo-location 권한 요청 헬퍼.

import * as Location from 'expo-location';

export interface LocationCoords {
  lat: number;
  lng: number;
}

export type LocationResult =
  | { ok: true; coords: LocationCoords }
  | { ok: false; reason: 'denied' | 'unavailable' | 'error'; message?: string };

export async function getCurrentLocation(): Promise<LocationResult> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      return { ok: false, reason: 'denied' };
    }
    const pos = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    return {
      ok: true,
      coords: { lat: pos.coords.latitude, lng: pos.coords.longitude },
    };
  } catch (e) {
    return {
      ok: false,
      reason: 'error',
      message: e instanceof Error ? e.message : 'unknown error',
    };
  }
}
