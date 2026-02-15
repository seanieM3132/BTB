from __future__ import annotations

from btb.db.connection import get_engine
from btb.db.schema import Base

def test_schema_create_all() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)

    # Basic sanity: tables exist in metadata
    expected = {
        "leagues",
        "seasons",
        "teams",
        "players",
        "games",
        "books",
        "odds_markets",
        "props_markets",
        "raw_provider",
        "bets",
        "clv_observations",
        "limits_snapshots",
        "play_by_play_events",
    }
    assert expected.issubset(set(Base.metadata.tables.keys()))
