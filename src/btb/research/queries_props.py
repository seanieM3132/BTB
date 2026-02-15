from __future__ import annotations

import datetime
from typing import Any, Dict

from sqlalchemy import and_

from btb.db.connection import get_session
from btb.db.schema import Book, Game, OddsMarket, Player, PropsMarket, Team


def get_player_prop_research(player_name: str, game_date: datetime.date) -> Dict[str, Any]:
    """
    v1 research bundle (DB-backed):
    - resolve player
    - locate game on game_date (by games that have props for this player)
    - return props across books + basic game context + main odds snapshot
    """
    s = get_session()

    # 1) resolve player (simple exact match for v1)
    player = s.query(Player).filter(Player.full_name == player_name).first()
    if not player:
        return {"ok": False, "reason": "PLAYER_NOT_FOUND", "player_name": player_name}

    # 2) locate game via props on that date
    game = (
        s.query(Game)
        .join(PropsMarket, PropsMarket.game_id == Game.id)
        .filter(and_(PropsMarket.player_id == player.id, Game.game_date == game_date))
        .first()
    )
    if not game:
        return {"ok": False, "reason": "NO_GAME_FOR_DATE", "player": player.full_name, "date": str(game_date)}

    home = s.query(Team).filter(Team.id == game.home_team_id).first()
    away = s.query(Team).filter(Team.id == game.away_team_id).first()

    # 3) props rows for this player + game
    props_rows = (
        s.query(PropsMarket, Book)
        .join(Book, Book.id == PropsMarket.book_id)
        .filter(and_(PropsMarket.game_id == game.id, PropsMarket.player_id == player.id))
        .all()
    )

    props_out = []
    for pm, bk in props_rows:
        props_out.append(
            {
                "book": bk.code,
                "prop_type": pm.prop_type,
                "line": pm.line,
                "price": pm.price,
                "source": pm.source,
            }
        )

    # 4) main odds for that game (all books)
    odds_rows = (
        s.query(OddsMarket, Book)
        .join(Book, Book.id == OddsMarket.book_id)
        .filter(OddsMarket.game_id == game.id)
        .all()
    )
    odds_out = []
    for om, bk in odds_rows:
        odds_out.append(
            {
                "book": bk.code,
                "market_type": om.market_type,
                "outcome": om.outcome,
                "line": om.line,
                "price": om.price,
                "source": om.source,
            }
        )

    return {
        "ok": True,
        "player": {"id": player.id, "name": player.full_name},
        "game": {
            "id": game.id,
            "external_id": game.external_id,
            "date": str(game.game_date),
            "home": home.name if home else None,
            "away": away.name if away else None,
            "season_type": game.season_type,
        },
        "props": props_out,
        "main_odds": odds_out,
    }
