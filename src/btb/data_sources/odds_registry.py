from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from btb.data_sources import odds_the_odds_api
from btb.data_sources.odds_normalize import normalize_the_odds_api_odds


def ingest_odds_with_fallbacks(league: str, day: dt.date) -> dict[str, Any]:
    """
    Try odds providers in order. Return first success (games_returned > 0),
    otherwise return merged degraded summary.
    """
    results: list[dict[str, Any]] = []

    r1 = odds_the_odds_api.ingest_day_main_markets(league, day)
    results.append({"provider": "the_odds_api", **r1})

    if isinstance(r1, dict) and r1.get("games_returned", 0) > 0:
        return {"ok": True, "used_provider": "the_odds_api", "result": r1}

    degraded_flags = []
    reason_counts: dict[str, int] = {}
    for r in results:
        rc = r.get("reason_code")
        if rc:
            degraded_flags.append(rc)
            reason_counts[rc] = reason_counts.get(rc, 0) + 1

    return {
        "ok": False,
        "used_provider": None,
        "results": results,
        "degraded_flags": degraded_flags,
        "reason_counts": reason_counts,
    }


def ingest_odds_from_fixture(path: str, league: str = "NBA") -> dict[str, Any]:
    """
    Load a saved The Odds API payload fixture and normalize it into DB.
    This keeps v1 buildable/testable without live provider access.
    """
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        return {"ok": False, "error": "fixture payload must be a JSON list"}
    norm = normalize_the_odds_api_odds(payload, league_code=league)
    return {"ok": True, "fixture": str(p), "normalized": norm}
