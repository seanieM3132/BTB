from __future__ import annotations

import datetime

from btb.research.queries_props import get_player_prop_research


def test_player_prop_research_includes_recent_form() -> None:
    bundle = get_player_prop_research("Jayson Tatum", datetime.date(2026, 2, 20))

    assert bundle["ok"] is True
    assert "recent_form" in bundle
    rf = bundle["recent_form"]

    assert "n" in rf
    assert "avg" in rf
    assert set(["minutes", "points", "rebounds", "assists"]).issubset(set(rf["avg"].keys()))
