# shared-types

OpenAPI 스키마 → TypeScript / Python 타입 코드 생성.

## 흐름

1. `apps/api`의 FastAPI가 `/openapi.json`을 노출.
2. 본 패키지는 그 스키마에서 타입을 생성:
   - TS: `openapi-typescript`
   - Python: 이미 pydantic로 정의되어 있으므로 별도 codegen 불필요.

## 명령

```bash
# 백엔드 기동 후
pnpm dlx openapi-typescript http://localhost:8000/openapi.json -o src/api.d.ts
```
