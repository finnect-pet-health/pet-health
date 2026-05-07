// W3-v2: 가까운 병원 검색 API client.

import { api } from './client';
import type { HospitalNearbyList } from './types';

export interface NearbyParams {
  lat: number;
  lng: number;
  radius_m?: number;
  limit?: number;
  specialty?: string; // W4-v2 triage 활용 예정
}

export async function searchHospitalsNearby(
  params: NearbyParams,
): Promise<HospitalNearbyList> {
  const res = await api.get<HospitalNearbyList>('/hospitals/nearby', {
    params: {
      lat: params.lat,
      lng: params.lng,
      radius_m: params.radius_m ?? 3000,
      limit: params.limit ?? 3,
      ...(params.specialty ? { specialty: params.specialty } : {}),
    },
  });
  return res.data;
}
