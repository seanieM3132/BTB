from __future__ import annotations

import datetime

from btb.research.queries_props import get_player_prop_research


def test_props_include_edge_bias_confidence() -> None:
    bundle = get_player_prop_research("Jayson Tatum", datetime.date(2026, 2, 20))
    assert bundle["ok"] is True

    props = bundle["props"]
    assert len(props) >= 1

    p0 = props[0]
    assert "recent_avg" in p0
    assert "edge" in p0
    assert "bias" in p0
    assert "confidence" in p0

    # Fixture expectations
    pts = [p for p in props if p["prop_type"] == "points"][0]
    assert pts["line"] == 28.5
    assert pts["recent_avg"] == 30.0
    assert pts["edge"] == 1.5
    assert pts["bias"] == "over"
    assert pts["confidence"] == "medium"
