// W1: Import smoke test for shared-types codegen.
// 실제 사용은 W2에서 src/api/auth.ts, families.ts 의 타입 정의를 점진 이행할 예정.
import type { paths } from '@petfinect/shared-types';

export type AuthKakaoBody =
  paths['/v1/auth/kakao']['post']['requestBody']['content']['application/json'];
