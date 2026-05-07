from __future__ import annotations

import logging
import os

import httpx  # noqa: F401 — imported for future wiring in W2 D3
from authlib.integrations.httpx_client import OAuth1Auth

from app.integrations.fatsecret import FoodItem, FoodProvider  # noqa: F401

logger = logging.getLogger(__name__)

BASE_URL = "https://platform.fatsecret.com/rest/server.api"


class RealFoodProvider:
    def __init__(self) -> None:
        client_id = os.environ.get("FATSECRET_CLIENT_ID")
        client_secret = os.environ.get("FATSECRET_CLIENT_SECRET")
        if not (client_id and client_secret):
            raise RuntimeError(
                "FATSECRET_CLIENT_ID/SECRET 환경변수 미설정 — factory가 mock으로 폴백해야 함"
            )
        self._auth = OAuth1Auth(
            client_id=client_id,
            client_secret=client_secret,
            signature_method="HMAC-SHA1",
            signature_type="QUERY",
        )

    async def search(self, q: str, locale: str = "ko_KR") -> list[FoodItem]:
        # TODO(5.10 D3): wire foods.search call
        logger.warning("RealFoodProvider.search called but not yet wired (W2 D3)")
        raise NotImplementedError("RealFoodProvider.search wired in W2 D3")

    async def get(self, food_id: str) -> FoodItem | None:
        logger.warning("RealFoodProvider.get called but not yet wired (W2 D3)")
        raise NotImplementedError("RealFoodProvider.get wired in W2 D3")
