from __future__ import annotations

import datetime

from btb.research.queries_props import get_player_prop_research
from btb.research.reports_explain import render_prop_report


def test_render_prop_report_contains_key_sections() -> None:
    bundle = get_player_prop_research("Jayson Tatum", datetime.date(2026, 2, 20))
    text = render_prop_report(bundle)

    assert "JAYSON TATUM" in text
    assert "Boston Celtics vs Miami Heat" in text
    assert "Recent Form" in text
    assert "Points 28.5" in text
    assert "Edge:" in text
    assert "Confidence:" in text
