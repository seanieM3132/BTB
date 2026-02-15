from __future__ import annotations

import json
from pathlib import Path

from btb.data_sources.props_normalize import normalize_props_fixture
from btb.db.connection import get_session
from btb.db.schema import PropsMarket


def test_props_fixture_normalize_is_idempotent() -> None:
    payload = json.loads(Path("tests/fixtures/props_sample.json").read_text(encoding="utf-8-sig"))

    s = get_session()
    before = s.query(PropsMarket).count()

    out1 = normalize_props_fixture(payload)
    mid = get_session().query(PropsMarket).count()

    out2 = normalize_props_fixture(payload)
    after = get_session().query(PropsMarket).count()

    # first run may create rows if DB is empty
    assert mid >= before
    # second run should not add any new rows
    assert after == mid
    assert out2["props_created"] == 0
    assert out2["props_skipped_duplicates"] >= 1
