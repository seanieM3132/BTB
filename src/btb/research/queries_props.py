from __future__ import annotations

import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, desc

from btb.db.connection import get_session
from btb.db.schema import Book, Game, OddsMarket, Player, PropsMarket, StatsPlayerGame, Team


def _team_name(session, team_id: int | None) -> str:
    if not team_id:
        return "?"
    t = session.query(Team).filter(Team.id == team_id).first()
    return t.name if t else "?"


def _book_code(session, book_id: int | None) -> str:
    if not book_id:
        return "unknown"
    b = session.query(Book).filter(Book.id == book_id).first()
    return b.code if b else str(book_id)


def _recent_form(session, player_id: int, as_of_date: datetime.date, n: int = 5) -> Dict[str, Any]:
    rows: List[StatsPlayerGame] = (
        session.query(StatsPlayerGame)
        .join(Game, Game.id == StatsPlayerGame.game_id)
        .filter(
            and_(
                StatsPlayerGame.player_id == player_id,
                Game.game_date <= as_of_date,
            )
        )
        .order_by(desc(Game.game_date))
        .limit(n)
        .all()
    )

    if not rows:
        return {"n": 0, "games": [], "avg": {"minutes": None, "points": None, "rebounds": None, "assists": None}}

    games = []
    mins = pts = reb = ast = 0.0

    for r in rows:
        g = session.query(Game).filter(Game.id == r.game_id).first()
        gdate = g.game_date.isoformat() if g and g.game_date else None
        games.append(
            {
                "date": gdate,
                "minutes": float(r.minutes or 0.0),
                "points": int(r.points or 0),
                "rebounds": int(r.rebounds or 0),
                "assists": int(r.assists or 0),
            }
        )
        mins += float(r.minutes or 0.0)
        pts += float(r.points or 0)
        reb += float(r.rebounds or 0)
        ast += float(r.assists or 0)

    n_games = len(rows)
    return {
        "n": n_games,
        "games": games,
        "avg": {
            "minutes": round(mins / n_games, 2),
            "points": round(pts / n_games, 2),
            "rebounds": round(reb / n_games, 2),
            "assists": round(ast / n_games, 2),
        },
    }


def get_player_prop_research(player_name: str, game_date: datetime.date) -> Dict[str, Any]:
    session = get_session()

    player = session.query(Player).filter(Player.full_name == player_name).first()
    if not player:
        return {"ok": False, "error": f"player not found: {player_name}"}

    game = session.query(Game).filter(Game.game_date == game_date).order_by(Game.id.desc()).first()
    if not game:
        pm = (
            session.query(PropsMarket)
            .filter(PropsMarket.player_id == player.id)
            .order_by(PropsMarket.id.desc())
            .first()
        )
        if pm:
            game = session.query(Game).filter(Game.id == pm.game_id).first()

    if not game:
        return {
            "ok": True,
            "player": {"id": player.id, "name": player.full_name},
            "game": None,
            "props": [],
            "main_odds": [],
            "recent_form": _recent_form(session, player.id, game_date),
        }

    home = _team_name(session, game.home_team_id)
    away = _team_name(session, game.away_team_id)

    props = (
        session.query(PropsMarket)
        .filter(and_(PropsMarket.game_id == game.id, PropsMarket.player_id == player.id))
        .order_by(PropsMarket.prop_type.asc(), PropsMarket.line.asc())
        .all()
    )

    props_out = []
    for p in props:
        props_out.append(
            {
                "book": _book_code(session, p.book_id),
                "prop_type": p.prop_type,
                "line": float(p.line),
                "price": float(p.price),
                "source": p.source,
            }
        )

    main = session.query(OddsMarket).filter(OddsMarket.game_id == game.id).all()
    main_out = []
    for m in main:
        main_out.append(
            {
                "book": _book_code(session, m.book_id),
                "market_type": m.market_type,
                "outcome": m.outcome,
                "line": (float(m.line) if m.line is not None else None),
                "price": float(m.price),
                "source": m.source,
            }
        )

    return {
        "ok": True,
        "player": {"id": player.id, "name": player.full_name},
        "game": {
            "id": game.id,
            "external_id": game.external_id,
            "date": game.game_date.isoformat() if game.game_date else None,
            "home": home,
            "away": away,
            "season_type": game.season_type,
        },
        "props": props_out,
        "main_odds": main_out,
        "recent_form": _recent_form(session, player.id, game_date),
    }
