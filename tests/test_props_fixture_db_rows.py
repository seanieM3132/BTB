from __future__ import annotations

import json
from pathlib import Path

from btb.data_sources.props_normalize import normalize_props_fixture
from btb.db.connection import get_session
from btb.db.schema import Player, PropsMarket


def test_props_fixture_normalize_creates_rows() -> None:
    payload = json.loads(Path("tests/fixtures/props_sample.json").read_text(encoding="utf-8-sig"))
    out = normalize_props_fixture(payload)
    assert out["props_created"] >= 1

    session = get_session()
    assert session.query(PropsMarket).count() >= 1
    assert session.query(Player).count() >= 1
