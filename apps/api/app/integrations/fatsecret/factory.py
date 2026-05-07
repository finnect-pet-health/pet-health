from __future__ import annotations

import os

from app.integrations.fatsecret import FoodProvider
from app.integrations.fatsecret.mock import MockFoodProvider


def get_food_provider() -> FoodProvider:
    use_mock = os.environ.get("FATSECRET_USE_MOCK", "1").lower() in ("1", "true", "yes")
    if use_mock:
        return MockFoodProvider()
    # Lazy import — RealFoodProvider raises if env vars missing
    from app.integrations.fatsecret.real import RealFoodProvider

    try:
        return RealFoodProvider()
    except RuntimeError:
        # graceful fallback
        return MockFoodProvider()
