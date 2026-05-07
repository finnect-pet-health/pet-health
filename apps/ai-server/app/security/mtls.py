"""mTLS SSLContext 빌더 + uvicorn ssl 옵션 dict 생성.

uvicorn 의 `ssl_*` 인자는 자체 SSL context 를 만들지 않고 string path 만 받지만,
require_mtls 강제 + cert_reqs 설정을 위해 명시적 ssl 모듈 사용도 지원.

Day 2 (W3-v2 plan §3.2 Track B):
- gen_dev_certs.sh 로 ca/server/client cert 발급
- 본 모듈로 uvicorn 부팅 시 ssl 옵션 wiring
- 통합 테스트는 별도 (uvicorn subprocess + httpx custom verify) — flaky 방지
"""
from __future__ import annotations

import ssl
from pathlib import Path
from typing import Any


class MTLSConfigError(ValueError):
    """ssl_certfile/keyfile/ca_certs 가 부분만 셋팅됐을 때."""


def build_uvicorn_ssl_kwargs(
    *,
    ssl_certfile: str,
    ssl_keyfile: str,
    ssl_ca_certs: str = "",
    require_mtls: bool = False,
) -> dict[str, Any]:
    """uvicorn.run(**kwargs) 에 풀어넣을 ssl 관련 dict.

    빈 값이면 빈 dict 반환 (HTTP 모드). cert/key 둘 중 하나만 셋이면 에러.
    require_mtls=True 인데 ssl_ca_certs 미설정 시 에러.
    """
    if not ssl_certfile and not ssl_keyfile:
        if ssl_ca_certs or require_mtls:
            raise MTLSConfigError(
                "ssl_ca_certs/require_mtls 셋팅됨에도 server cert/key 미설정"
            )
        return {}

    if not ssl_certfile or not ssl_keyfile:
        raise MTLSConfigError(
            f"ssl_certfile={ssl_certfile!r} ssl_keyfile={ssl_keyfile!r} — 둘 다 필요"
        )

    for label, p in (
        ("ssl_certfile", ssl_certfile),
        ("ssl_keyfile", ssl_keyfile),
    ):
        if not Path(p).exists():
            raise MTLSConfigError(f"{label}={p!r} 파일 부재")

    out: dict[str, Any] = {
        "ssl_certfile": ssl_certfile,
        "ssl_keyfile": ssl_keyfile,
    }
    if ssl_ca_certs:
        if not Path(ssl_ca_certs).exists():
            raise MTLSConfigError(f"ssl_ca_certs={ssl_ca_certs!r} 파일 부재")
        out["ssl_ca_certs"] = ssl_ca_certs
        out["ssl_cert_reqs"] = (
            ssl.CERT_REQUIRED if require_mtls else ssl.CERT_OPTIONAL
        )
    elif require_mtls:
        raise MTLSConfigError("require_mtls=True 인데 ssl_ca_certs 미설정")

    return out


def build_client_ssl_context(
    *,
    ssl_ca_certs: str,
    client_certfile: str = "",
    client_keyfile: str = "",
) -> ssl.SSLContext:
    """클라우드 백엔드 측 httpx 검증 컨텍스트.

    cloud → AI 서버 호출 시 사용. ca 로 서버 cert 검증, client cert 로 자기 자신
    인증 (mTLS).
    """
    ctx = ssl.create_default_context(cafile=ssl_ca_certs)
    if client_certfile and client_keyfile:
        ctx.load_cert_chain(certfile=client_certfile, keyfile=client_keyfile)
    return ctx
