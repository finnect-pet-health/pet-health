// 모바일 RN 환경에서 파일 URI → Uint8Array 변환.
// expo-camera/expo-av 가 반환하는 fileUri 를 backend PUT body 로 변환할 때 사용.

import * as FileSystem from 'expo-file-system';

export async function readFileAsBytes(uri: string): Promise<Uint8Array> {
  const base64 = await FileSystem.readAsStringAsync(uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  // RN polyfill 의 atob 사용. 미설치 환경이면 Buffer 폴백.
  const decode: (s: string) => string =
    typeof globalThis.atob === 'function'
      ? globalThis.atob.bind(globalThis)
      : (s) => Buffer.from(s, 'base64').toString('binary');
  const binary = decode(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}
