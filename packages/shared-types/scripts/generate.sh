#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# OpenAPI 스냅샷 우선순위: 최신 W3-v2 → W2 → W1.
SCHEMA_FILE=""
for candidate in \
  ../../docs/api/openapi-w3-v2.json \
  ../../docs/api/openapi-w2-v2.json \
  ../../docs/api/openapi-w1.json; do
  if [[ -f "$candidate" ]]; then
    SCHEMA_FILE="$candidate"
    break
  fi
done
if [[ -z "$SCHEMA_FILE" ]]; then
  echo "no openapi-*.json snapshot found in docs/api/" >&2
  exit 1
fi
echo "Using schema: $SCHEMA_FILE"
npx --yes openapi-typescript "$SCHEMA_FILE" -o generated/api.ts
echo "Generated generated/api.ts"
