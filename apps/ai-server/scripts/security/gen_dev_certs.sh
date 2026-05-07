#!/usr/bin/env bash
# 자체 서명 인증서 발급 (dev/CI 한정).
#
# 산출:
#   ${OUT_DIR}/ca.{key,crt}     — Root CA
#   ${OUT_DIR}/server.{key,crt} — AI server 인증서 (CN=ai-server.local)
#   ${OUT_DIR}/client.{key,crt} — 클라우드 백엔드 client 인증서 (CN=cloud-api)
#
# uvicorn 부팅:
#   uvicorn app.main:app \
#     --ssl-certfile=${OUT_DIR}/server.crt \
#     --ssl-keyfile=${OUT_DIR}/server.key \
#     --ssl-ca-certs=${OUT_DIR}/ca.crt
#
# 클라이언트(httpx) 검증:
#   httpx.AsyncClient(verify=str(ca_path), cert=(client.crt, client.key))
#
# 본 스크립트는 dev only — Cloudflare Tunnel 운영 인증서는 별도 provisioning.

set -euo pipefail

OUT_DIR="${1:-${PWD}/.dev-certs}"
DAYS="${DAYS:-365}"
KEY_BITS="${KEY_BITS:-2048}"

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl 미설치 — apt/brew 로 설치 후 재시도" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
cd "${OUT_DIR}"

# 1. Root CA
openssl genrsa -out ca.key ${KEY_BITS} 2>/dev/null
openssl req -x509 -new -nodes -key ca.key -sha256 -days ${DAYS} \
  -subj "/CN=PetFinect Dev CA" -out ca.crt 2>/dev/null
echo "[+] ca.crt + ca.key 생성"

# 2. Server cert (signed by CA)
openssl genrsa -out server.key ${KEY_BITS} 2>/dev/null
openssl req -new -key server.key -subj "/CN=ai-server.local" -out server.csr 2>/dev/null
cat > server.ext <<EOF
subjectAltName = DNS:ai-server.local, DNS:localhost, IP:127.0.0.1
extendedKeyUsage = serverAuth
EOF
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days ${DAYS} -sha256 -extfile server.ext 2>/dev/null
rm -f server.csr server.ext
echo "[+] server.crt + server.key 생성 (CN=ai-server.local)"

# 3. Client cert (cloud-api)
openssl genrsa -out client.key ${KEY_BITS} 2>/dev/null
openssl req -new -key client.key -subj "/CN=cloud-api" -out client.csr 2>/dev/null
cat > client.ext <<EOF
extendedKeyUsage = clientAuth
EOF
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days ${DAYS} -sha256 -extfile client.ext 2>/dev/null
rm -f client.csr client.ext
echo "[+] client.crt + client.key 생성 (CN=cloud-api)"

chmod 600 *.key
echo "✅ 완료 — ${OUT_DIR}"
ls -la "${OUT_DIR}"
