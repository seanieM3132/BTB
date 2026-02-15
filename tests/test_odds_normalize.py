from __future__ import annotations

from btb.data_sources.odds_normalize import normalize_the_odds_api_odds

def test_normalize_empty_payload() -> None:
    out = normalize_the_odds_api_odds([])
    assert out["games_created"] == 0
    assert out["markets_created"] == 0
    assert out["books_seen"] == []
