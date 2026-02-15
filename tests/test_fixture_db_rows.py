from __future__ import annotations

import json
from pathlib import Path

from btb.data_sources.odds_normalize import normalize_the_odds_api_odds
from btb.db.connection import get_session
from btb.db.schema import Book, Game, OddsMarket, Team


def test_fixture_creates_or_upserts_rows() -> None:
    # fixture may contain a BOM; read safely
    payload = json.loads(Path("tests/fixtures/the_odds_api_sample.json").read_text(encoding="utf-8-sig"))

    # run normalization (should be safe to run multiple times)
    _ = normalize_the_odds_api_odds(payload)

    session = get_session()

    # assert the database has the expected minimum entities
    assert session.query(Game).count() >= 1
    assert session.query(Team).count() >= 2
    assert session.query(Book).count() >= 1
    assert session.query(OddsMarket).count() >= 1
