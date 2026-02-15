from __future__ import annotations

import datetime

from btb.research.queries_props import get_player_prop_research
from btb.research.reports_explain import render_prop_report


def test_report_includes_main_markets_when_present() -> None:
    bundle = get_player_prop_research("Jayson Tatum", datetime.date(2026, 2, 20))
    text = render_prop_report(bundle)
    assert "Main Markets" in text
    assert "ML" in text or "SPREAD" in text or "TOTAL" in text
