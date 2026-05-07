"""uvicorn 부팅 entrypoint — settings.ssl_* 가 셋팅되면 mTLS 활성.

사용:
    python -m app.serve              # 일반 HTTP
    SSL_CERTFILE=... SSL_KEYFILE=... SSL_CA_CERTS=... REQUIRE_MTLS=1 \
        python -m app.serve          # mTLS

(.env 파일에 셋팅하면 동일.)
"""
from __future__ import annotations

import argparse

import uvicorn

from app.config import settings
from app.security.mtls import build_uvicorn_ssl_kwargs


def main() -> int:
    parser = argparse.ArgumentParser(description="PetFinect AI server (uvicorn)")
    parser.add_argument("--host", default="0.0.0.0")  # noqa: S104
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    ssl_kwargs = build_uvicorn_ssl_kwargs(
        ssl_certfile=settings.ssl_certfile,
        ssl_keyfile=settings.ssl_keyfile,
        ssl_ca_certs=settings.ssl_ca_certs,
        require_mtls=settings.require_mtls,
    )
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        **ssl_kwargs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
