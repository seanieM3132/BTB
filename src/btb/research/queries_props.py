from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select

from btb.db.connection import get_session
from btb.db.schema import Book, Game, OddsMarket, Player, PropsMarket, StatsPlayerGame, Team


def _norm_name(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _get_player_by_name(session, player_name: str) -> Optional[Player]:
    pn = _norm_name(player_name)
    if not pn:
        return None

    players = session.execute(select(Player)).scalars().all()

    for p in players:
        if _norm_name(p.full_name) == pn:
            return p

    for p in players:
        if pn in _norm_name(p.full_name):
            return p

    return None


def _get_game_for_player_on_date(session, player_id: int, game_date: datetime.date) -> Optional[Game]:
    player = session.get(Player, player_id)
    if player is None:
        return None

    games = session.execute(select(Game).where(Game.game_date == game_date)).scalars().all()
    if not games:
        return None

    if player.team_id:
        for g in games:
            if g.home_team_id == player.team_id or g.away_team_id == player.team_id:
                return g

    return games[0]


def _load_recent_stats(session, player_id: int, upto_date: datetime.date, max_games: int = 10) -> List[StatsPlayerGame]:
    rows = session.execute(
        select(StatsPlayerGame)
        .join(Game, StatsPlayerGame.game_id == Game.id)
        .where(StatsPlayerGame.player_id == player_id)
        .where(Game.game_date <= upto_date)
        .order_by(Game.game_date.desc())
        .limit(max_games)
    ).scalars().all()
    return rows


def _avg_from_stats(rows: List[StatsPlayerGame]) -> Dict[str, float]:
    if not rows:
        return {}
    n = len(rows)
    mins = sum(float(r.minutes or 0.0) for r in rows) / n
    pts = sum(float(r.points or 0.0) for r in rows) / n
    reb = sum(float(r.rebounds or 0.0) for r in rows) / n
    ast = sum(float(r.assists or 0.0) for r in rows) / n
    return {"minutes": mins, "points": pts, "rebounds": reb, "assists": ast}


def _stat_value_for_prop(row: StatsPlayerGame, prop_type: str) -> Optional[float]:
    pt = (prop_type or "").lower().strip()
    if pt in ("points", "pts"):
        return float(row.points or 0.0)
    if pt in ("rebounds", "rebs", "reb"):
        return float(row.rebounds or 0.0)
    if pt in ("assists", "asts", "ast"):
        return float(row.assists or 0.0)
    return None


def _hit_rate(rows: List[StatsPlayerGame], prop_type: str, line: float) -> Optional[float]:
    vals: List[float] = []
    for r in rows:
        v = _stat_value_for_prop(r, prop_type)
        if v is None:
            continue
        vals.append(v)
    if not vals:
        return None
    hits = sum(1 for v in vals if v > float(line))
    return hits / len(vals)


def _bias_and_conf(edge: float, hit_rate_5: Optional[float]) -> Tuple[str, str]:
    # Bias is directional on edge
    bias = "over" if edge >= 0 else "under"

    # IMPORTANT: tests expect confidence based on edge only (no hit-rate boost)
    abs_edge = abs(edge)
    if abs_edge >= 2.0:
        conf = "high"
    elif abs_edge >= 1.0:
        conf = "medium"
    else:
        conf = "low"

    return bias, conf


def get_player_prop_research(player_name: str, game_date: datetime.date) -> Dict[str, Any]:
    """
    Structured research bundle for a player's props on a date.

    Test contract expectations:
    - Each prop includes: recent_avg, edge, bias, confidence
    - recent_form includes top-level keys: n, avg
    """
    session = get_session()

    player = _get_player_by_name(session, player_name)
    if player is None:
        return {"ok": False, "error": f"Player not found: {player_name}"}

    game = _get_game_for_player_on_date(session, player.id, game_date)
    if game is None:
        return {"ok": False, "error": f"No game found on {game_date.isoformat()} for {player.full_name}"}

    home_team = session.get(Team, game.home_team_id) if game.home_team_id else None
    away_team = session.get(Team, game.away_team_id) if game.away_team_id else None

    recent_rows_10 = _load_recent_stats(session, player.id, game_date, max_games=10)
    recent_rows_5 = recent_rows_10[:5]
    recent_rows_1 = recent_rows_10[:1]

    avg10 = _avg_from_stats(recent_rows_10)

    recent_form = {
        # tests expect these at top-level
        "n": len(recent_rows_10),
        "avg": avg10,
        # windows (used by report/tests)
        "last_1": {"n": len(recent_rows_1), "avg": _avg_from_stats(recent_rows_1)},
        "last_5": {"n": len(recent_rows_5), "avg": _avg_from_stats(recent_rows_5)},
        "last_10": {"n": len(recent_rows_10), "avg": avg10},
        "games": [
            {
                "date": (session.get(Game, r.game_id).game_date.isoformat() if session.get(Game, r.game_id) else None),
                "minutes": float(r.minutes or 0.0),
                "points": int(r.points or 0),
                "rebounds": int(r.rebounds or 0),
                "assists": int(r.assists or 0),
            }
            for r in recent_rows_10
        ],
    }

    props = session.execute(
        select(PropsMarket).where(PropsMarket.game_id == game.id).where(PropsMarket.player_id == player.id)
    ).scalars().all()

    props_out: List[Dict[str, Any]] = []
    for p in props:
        book_obj = session.get(Book, p.book_id) if p.book_id is not None else None
        book_code = book_obj.code if book_obj is not None else None

        stat_vals_5: List[float] = []
        for r in recent_rows_5:
            v = _stat_value_for_prop(r, p.prop_type)
            if v is not None:
                stat_vals_5.append(v)

        recent_avg_5: Optional[float] = None
        if stat_vals_5:
            recent_avg_5 = sum(stat_vals_5) / len(stat_vals_5)

        edge: Optional[float] = None
        if recent_avg_5 is not None and p.line is not None:
            edge = float(recent_avg_5) - float(p.line)

        hr5: Optional[float] = None
        if p.line is not None:
            hr5 = _hit_rate(recent_rows_5, p.prop_type, float(p.line))

        bias: Optional[str] = None
        confidence: Optional[str] = None
        if edge is not None:
            bias, confidence = _bias_and_conf(edge, hr5)

        props_out.append(
            {
                "book": book_code,
                "prop_type": p.prop_type,
                "line": float(p.line) if p.line is not None else None,
                "price": float(p.price) if p.price is not None else None,

                # tests expect this key
                "recent_avg": float(recent_avg_5) if recent_avg_5 is not None else None,

                # extra fields are fine
                "recent_avg_5": float(recent_avg_5) if recent_avg_5 is not None else None,
                "edge": float(edge) if edge is not None else None,
                "hit_rate_5": float(hr5) if hr5 is not None else None,
                "bias": bias,
                "confidence": confidence,
                "source": p.source,
            }
        )

    main = session.execute(select(OddsMarket).where(OddsMarket.game_id == game.id)).scalars().all()

    seen_main = set()
    main_out: List[Dict[str, Any]] = []
    for m in main:
        book_obj = session.get(Book, m.book_id) if m.book_id is not None else None
        book_code = book_obj.code if book_obj is not None else None

        key = (
            book_code,
            m.market_type,
            m.outcome,
            float(m.line) if m.line is not None else None,
            float(m.price) if m.price is not None else None,
            m.source,
        )
        if key in seen_main:
            continue
        seen_main.add(key)

        main_out.append(
            {
                "book": book_code,
                "market_type": m.market_type,
                "outcome": m.outcome,
                "line": float(m.line) if m.line is not None else None,
                "price": float(m.price) if m.price is not None else None,
                "source": m.source,
            }
        )

    return {
        "ok": True,
        "player": {"id": player.id, "name": player.full_name},
        "game": {
            "id": game.id,
            "external_id": game.external_id,
            "date": game.game_date.isoformat(),
            "home": home_team.name if home_team else "HOME",
            "away": away_team.name if away_team else "AWAY",
            "season_type": game.season_type,
        },
        "props": props_out,
        "main_odds": main_out,
        "recent_form": recent_form,
    }
