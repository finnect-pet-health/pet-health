// W3-v2: presigned upload helpers.
// `presignUpload` 은 백엔드에 키를 발급받음. `uploadToPresignedUrl` 은 받은 URL 로
// PUT 하여 객체를 적재. 실 운영(S3)에서는 presign URL 이 직접 S3 로 가지만,
// dev/mock 환경(`mock-s3://` 스킴)에서는 backend `/v1/uploads/raw` 라우트로 forward.

import { api } from './client';
import type { PresignBody, PresignResponse } from './types';

export async function presignUpload(body: PresignBody): Promise<PresignResponse> {
  const res = await api.post<PresignResponse>('/uploads/presign', body);
  return res.data;
}

const MOCK_URL_PATTERN = /^mock-s3:\/\/[^/]+\/([^?]+)/;

/**
 * presigned URL 로 파일 PUT.
 *
 * - 실 S3 URL → 직접 PUT (Authorization 헤더 없음)
 * - `mock-s3://` URL → key 추출 후 backend `/v1/uploads/raw?key=...` 로 POST
 *   (api 인스턴스 통해 인증 헤더 자동 부착)
 *
 * @param url presignUpload 응답의 url
 * @param body PUT body (Blob, Uint8Array, ArrayBuffer 등 fetch 가 받는 형식)
 * @param contentType presign 요청 시 사용한 content_type 과 동일해야 함
 */
export async function uploadToPresignedUrl(
  url: string,
  body: BodyInit,
  contentType: string,
): Promise<void> {
  const mockMatch = url.match(MOCK_URL_PATTERN);
  if (mockMatch) {
    const key = decodeURIComponent(mockMatch[1]);
    await api.post('/uploads/raw', body, {
      params: { key },
      headers: { 'Content-Type': contentType },
    });
    return;
  }
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': contentType },
    body,
  });
  if (!res.ok) {
    throw new Error(`presigned upload failed: ${res.status}`);
  }
}
