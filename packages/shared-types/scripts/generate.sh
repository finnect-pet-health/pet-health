#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
npx --yes openapi-typescript ../../docs/api/openapi-w1.json -o generated/api.ts
echo "Generated generated/api.ts"
