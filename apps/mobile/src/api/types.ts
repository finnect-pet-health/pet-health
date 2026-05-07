// shared-types codegen import + 도메인별 타입 alias.
// 모든 alias 는 paths['/v1/...']['method']['requestBody|responses'] 에서 도출 →
// API 스키마가 변경되면 codegen 후 즉시 컴파일 에러로 회귀 검출.

import type { paths } from '@petfinect/shared-types';

// ---- Auth ----
export type AuthKakaoBody =
  paths['/v1/auth/kakao']['post']['requestBody']['content']['application/json'];

// ---- Uploads (presigned) ----
export type PresignBody =
  paths['/v1/uploads/presign']['post']['requestBody']['content']['application/json'];
export type PresignResponse =
  paths['/v1/uploads/presign']['post']['responses']['200']['content']['application/json'];

// ---- Diagnose ----
export type DiagnoseImageBody =
  paths['/v1/diagnose/image']['post']['requestBody']['content']['application/json'];
export type DiagnoseAudioBody =
  paths['/v1/diagnose/audio']['post']['requestBody']['content']['application/json'];
export type DiagnosisOut =
  paths['/v1/diagnose/image']['post']['responses']['200']['content']['application/json'];
export type DiagnosesList =
  paths['/v1/pets/{pet_id}/diagnoses']['get']['responses']['200']['content']['application/json'];

// ---- Hospitals ----
export type HospitalNearbyList =
  paths['/v1/hospitals/nearby']['get']['responses']['200']['content']['application/json'];
