from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional

import requests

from btb.core.config import get_settings
from btb.db.connection import get_session
from btb.db.schema import RawProvider


SPORTS_URL = "https://api.the-odds-api.com/v4/sports"
ODDS_URL_TMPL = "https://api.the-odds-api.com/v4/sports/{sport_key}/odds"


def _discover_sport_keys(api_key: str) -> list[dict[str, Any]]:
    r = requests.get(SPORTS_URL, params={"apiKey": api_key}, timeout=20)
    r.raise_for_status()
    return r.json()


def resolve_nba_sport_key(api_key: str) -> Optional[str]:
    """
    Prefer basketball_nba if available; otherwise return None.
    """
    sports = _discover_sport_keys(api_key)
    keys = {s.get("key") for s in sports if s.get("key")}
    if "basketball_nba" in keys:
        return "basketball_nba"
    return None


def ingest_day_main_markets(league: str, day: dt.date, sport_key: Optional[str] = None) -> dict[str, Any]:
    settings = get_settings()
    if not settings.odds_api_key:
        return {"error": "THE_ODDS_API_KEY not set", "reason_code": "ODDS_PROVIDER_DOWN"}

    api_key = settings.odds_api_key
    resolved = sport_key or resolve_nba_sport_key(api_key)

    if not resolved:
        return {
            "error": "No accessible sport key for NBA main odds (basketball_nba not available for this API key).",
            "reason_code": "ODDS_PROVIDER_DOWN",
            "accessible_nba_keys": ["basketball_nba_all_stars", "basketball_nba_championship_winner"],
        }

    url = ODDS_URL_TMPL.format(sport_key=resolved)

    params = {
        "apiKey": api_key,
        "regions": "au,us,uk",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"API request failed: {e}", "reason_code": "ODDS_PROVIDER_DOWN", "sport_key": resolved}

    session = get_session()
    session.add(
        RawProvider(
            provider_name="the_odds_api",
            payload_json=json.dumps(data, ensure_ascii=False),
            scope="odds",
        )
    )
    session.commit()

    return {"league": league, "scope_date": str(day), "sport_key": resolved, "games_returned": len(data)}
