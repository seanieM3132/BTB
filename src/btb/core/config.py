from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    odds_api_key: str | None


def get_settings() -> Settings:
    return Settings(
        odds_api_key=os.getenv("THE_ODDS_API_KEY"),
    )
