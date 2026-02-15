from __future__ import annotations

import json
from pathlib import Path

from btb.data_sources.odds_normalize import normalize_the_odds_api_odds
from btb.db.connection import get_session
from btb.db.schema import Game, OddsMarket, Team, Book


def test_fixture_creates_rows(tmp_path) -> None:
    # load the repo fixture
    payload = json.loads(Path("tests/fixtures/the_odds_api_sample.json").read_text(encoding="utf-8"))

    out = normalize_the_odds_api_odds(payload)

    session = get_session()

    assert out["games_created"] >= 1
    assert session.query(Game).count() >= 1
    assert session.query(Team).count() >= 2
    assert session.query(Book).count() >= 1
    assert session.query(OddsMarket).count() >= 1
