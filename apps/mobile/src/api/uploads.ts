// W3-v2: presigned upload helpers.
// `presignUpload` 은 백엔드에 키를 발급받음. `uploadToPresignedUrl` 은 받은 URL 로
// PUT 하여 객체를 적재. 실 운영(S3)에서는 presign URL 이 직접 S3 로 가지만,
// dev/mock 환경에서는 `mock-s3://` 스킴 URL 이 반환됨 → 실 PUT 은 LocalStack
// 도입(W3-v2 D2) 또는 별도 dev raw upload 라우트 도입 시점에 마무리.

import { api } from './client';
import type { PresignBody, PresignResponse } from './types';

export async function presignUpload(body: PresignBody): Promise<PresignResponse> {
  const res = await api.post<PresignResponse>('/uploads/presign', body);
  return res.data;
}

/**
 * presigned URL 로 파일 PUT.
 *
 * @param url presignUpload 응답의 url
 * @param body PUT body (Blob, Uint8Array, ArrayBuffer 등 fetch 가 받는 형식)
 * @param contentType presign 요청 시 사용한 content_type 과 동일해야 함
 *
 * mock-s3:// 스킴은 LocalStack 도입 전까지 no-op (개발용 placeholder).
 */
export async function uploadToPresignedUrl(
  url: string,
  body: BodyInit,
  contentType: string,
): Promise<void> {
  if (url.startsWith('mock-s3://')) {
    // TODO(W3-v2 D2): LocalStack 또는 backend `/uploads/raw` 라우트로 라우팅.
    // 현재는 in-memory mock storage 라 PUT 결과를 받을 수 없음.
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
