"""W3-v2 AC6 mTLS — uvicorn ssl 옵션 dict + 클라이언트 SSLContext 빌더 검증.

실 handshake 통합 테스트 (uvicorn subprocess + httpx custom verify) 는 D2 정규
작업으로 별도 — 본 케이스는 cert 로딩 + dict 구성 + 분기 검증만.
"""
from __future__ import annotations

import shutil
import ssl
import subprocess
from pathlib import Path

import pytest

from app.security.mtls import (
    MTLSConfigError,
    build_client_ssl_context,
    build_uvicorn_ssl_kwargs,
)


@pytest.fixture(scope="module")
def dev_certs(tmp_path_factory) -> Path:
    """gen_dev_certs.sh 로 임시 cert 발급. 이후 케이스는 산출물을 공유."""
    if shutil.which("openssl") is None:
        pytest.skip("openssl 미설치 — mTLS 테스트 skip")

    out = tmp_path_factory.mktemp("dev-certs")
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "security" / "gen_dev_certs.sh"
    )
    result = subprocess.run(
        ["bash", str(script), str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"gen_dev_certs.sh 실패: {result.stderr}")
    for name in ("ca.crt", "server.crt", "server.key", "client.crt", "client.key"):
        assert (out / name).exists(), f"{name} 미생성"
    return out


def test_empty_config_returns_empty_dict() -> None:
    assert build_uvicorn_ssl_kwargs(ssl_certfile="", ssl_keyfile="") == {}


def test_partial_cert_key_raises() -> None:
    with pytest.raises(MTLSConfigError, match="둘 다 필요"):
        build_uvicorn_ssl_kwargs(ssl_certfile="server.crt", ssl_keyfile="")


def test_require_mtls_without_ca_raises(dev_certs) -> None:
    with pytest.raises(MTLSConfigError, match="ssl_ca_certs 미설정"):
        build_uvicorn_ssl_kwargs(
            ssl_certfile=str(dev_certs / "server.crt"),
            ssl_keyfile=str(dev_certs / "server.key"),
            require_mtls=True,
        )


def test_missing_cert_file_raises(dev_certs) -> None:
    with pytest.raises(MTLSConfigError, match="파일 부재"):
        build_uvicorn_ssl_kwargs(
            ssl_certfile=str(dev_certs / "does-not-exist.crt"),
            ssl_keyfile=str(dev_certs / "server.key"),
        )


def test_full_mtls_kwargs_structure(dev_certs) -> None:
    out = build_uvicorn_ssl_kwargs(
        ssl_certfile=str(dev_certs / "server.crt"),
        ssl_keyfile=str(dev_certs / "server.key"),
        ssl_ca_certs=str(dev_certs / "ca.crt"),
        require_mtls=True,
    )
    assert out["ssl_certfile"].endswith("server.crt")
    assert out["ssl_keyfile"].endswith("server.key")
    assert out["ssl_ca_certs"].endswith("ca.crt")
    assert out["ssl_cert_reqs"] == ssl.CERT_REQUIRED


def test_optional_mtls_when_require_false(dev_certs) -> None:
    out = build_uvicorn_ssl_kwargs(
        ssl_certfile=str(dev_certs / "server.crt"),
        ssl_keyfile=str(dev_certs / "server.key"),
        ssl_ca_certs=str(dev_certs / "ca.crt"),
        require_mtls=False,
    )
    assert out["ssl_cert_reqs"] == ssl.CERT_OPTIONAL


def test_tls_only_without_ca_omits_cert_reqs(dev_certs) -> None:
    out = build_uvicorn_ssl_kwargs(
        ssl_certfile=str(dev_certs / "server.crt"),
        ssl_keyfile=str(dev_certs / "server.key"),
    )
    assert "ssl_ca_certs" not in out
    assert "ssl_cert_reqs" not in out


def test_client_ssl_context_loads_ca(dev_certs) -> None:
    ctx = build_client_ssl_context(ssl_ca_certs=str(dev_certs / "ca.crt"))
    assert isinstance(ctx, ssl.SSLContext)
    # check_hostname 기본값 True (client 검증)
    assert ctx.check_hostname is True


def test_client_ssl_context_with_client_cert(dev_certs) -> None:
    ctx = build_client_ssl_context(
        ssl_ca_certs=str(dev_certs / "ca.crt"),
        client_certfile=str(dev_certs / "client.crt"),
        client_keyfile=str(dev_certs / "client.key"),
    )
    # 컨텍스트 생성 자체가 성공해야 cert chain 로딩 OK
    assert isinstance(ctx, ssl.SSLContext)
