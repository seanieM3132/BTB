from __future__ import annotations

import datetime
from typing import Dict, Any

from btb.db.connection import get_session
from btb.db.schema import Player, Game, PropsMarket


def get_player_prop_research(player_name: str, game_date: datetime.date) -> Dict[str, Any]:
    """
    Return minimal research bundle (stub v1).
    """
    session = get_session()

    player = session.query(Player).filter(Player.full_name.ilike(f"%{player_name}%")).first()

    if not player:
        return {"error": "Player not found"}

    games = session.query(Game).filter(Game.game_date == game_date).all()

    return {
        "player": player.full_name,
        "game_date": str(game_date),
        "games_found": len(games),
        "props_count": 0,
    }
