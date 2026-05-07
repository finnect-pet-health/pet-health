// W3-v2: diagnose API + uploadAndDiagnose orchestrator.
// 흐름: presign → 파일 PUT → POST /diagnose/{modality} → 결과 카드.
// 모바일 진단 화면(camera.tsx, audio.tsx) 는 본 헬퍼만 사용.

import { api } from './client';
import { presignUpload, uploadToPresignedUrl } from './uploads';
import type {
  DiagnoseAudioBody,
  DiagnoseImageBody,
  DiagnosesList,
  DiagnosisOut,
} from './types';

export type ImageRegion = 'skin' | 'eye' | 'ear' | 'gum';

export interface UploadAndDiagnoseImageArgs {
  petId: string;
  region: ImageRegion;
  fileUri: string;
  contentType: 'image/jpeg' | 'image/png';
  /** RN 환경에서 fileUri → fetch body 변환 (Blob/Uint8Array 등). */
  loadBody: (fileUri: string) => Promise<BodyInit>;
}

export interface UploadAndDiagnoseAudioArgs {
  petId: string;
  fileUri: string;
  contentType: 'audio/wav' | 'audio/mpeg' | 'audio/m4a' | 'audio/mp4';
  loadBody: (fileUri: string) => Promise<BodyInit>;
}

export async function diagnoseImage(body: DiagnoseImageBody): Promise<DiagnosisOut> {
  const res = await api.post<DiagnosisOut>('/diagnose/image', body);
  return res.data;
}

export async function diagnoseAudio(body: DiagnoseAudioBody): Promise<DiagnosisOut> {
  const res = await api.post<DiagnosisOut>('/diagnose/audio', body);
  return res.data;
}

export async function listPetDiagnoses(
  petId: string,
  limit = 20,
): Promise<DiagnosesList> {
  const res = await api.get<DiagnosesList>(`/pets/${petId}/diagnoses`, {
    params: { limit },
  });
  return res.data;
}

/**
 * presign → PUT → diagnose 단일 함수.
 * mock-s3:// 환경에서는 PUT 이 no-op 이므로, mock storage 에 사전 적재된
 * 객체 키를 의미만 갖는다(현재 dev 흐름은 raw 라우트 도입 후 완성).
 */
export async function uploadAndDiagnoseImage(
  args: UploadAndDiagnoseImageArgs,
): Promise<DiagnosisOut> {
  const { key, url } = await presignUpload({
    modality: 'image',
    content_type: args.contentType,
  });
  const body = await args.loadBody(args.fileUri);
  await uploadToPresignedUrl(url, body, args.contentType);
  return diagnoseImage({
    pet_id: args.petId,
    image_s3_key: key,
    region: args.region,
  });
}

export async function uploadAndDiagnoseAudio(
  args: UploadAndDiagnoseAudioArgs,
): Promise<DiagnosisOut> {
  const { key, url } = await presignUpload({
    modality: 'audio',
    content_type: args.contentType,
  });
  const body = await args.loadBody(args.fileUri);
  await uploadToPresignedUrl(url, body, args.contentType);
  return diagnoseAudio({
    pet_id: args.petId,
    audio_s3_key: key,
  });
}
