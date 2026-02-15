from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_

from btb.db.connection import get_session
from btb.db.schema import Game, League, Player, Season, StatsPlayerGame, Team


def _get_or_create_team(session, name: str) -> Team:
    team = session.query(Team).filter(Team.name == name).first()
    if team:
        return team
    team = Team(name=name, abbreviation=None, external_id=None)
    session.add(team)
    session.flush()
    return team


def _get_or_create_league(session, league_code: str) -> League:
    league = session.query(League).filter(League.code == league_code).first()
    if league:
        return league
    league = League(code=league_code, name=league_code)
    session.add(league)
    session.flush()
    return league


def _get_or_create_season(session, league_id: int, year_start: int, year_end: int) -> Season:
    season = (
        session.query(Season)
        .filter(and_(Season.league_id == league_id, Season.year_start == year_start, Season.year_end == year_end))
        .first()
    )
    if season:
        return season
    season = Season(league_id=league_id, year_start=year_start, year_end=year_end)
    session.add(season)
    session.flush()
    return season


def _infer_season_from_commence(commence_time: str) -> tuple[int, int]:
    dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
    year_start = dt.year if dt.month >= 10 else dt.year - 1
    return year_start, year_start + 1


def _get_or_create_game(
    session,
    external_id: str,
    league_id: int,
    season_id: int,
    commence_time: str,
    home_team: str,
    away_team: str,
) -> Game:
    g = session.query(Game).filter(Game.external_id == external_id).first()
    if g:
        return g

    dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
    home = _get_or_create_team(session, home_team)
    away = _get_or_create_team(session, away_team)

    g = Game(
        external_id=external_id,
        league_id=league_id,
        season_id=season_id,
        game_date=dt.date(),
        home_team_id=home.id,
        away_team_id=away.id,
        season_type="regular",
    )
    session.add(g)
    session.flush()
    return g


def _get_or_create_player(session, full_name: str) -> Player:
    p = session.query(Player).filter(Player.full_name == full_name).first()
    if p:
        return p
    p = Player(full_name=full_name, external_id=None, position=None, team_id=None)
    session.add(p)
    session.flush()
    return p


def _stat_row_exists(session, game_id: int, player_id: int) -> bool:
    return session.query(StatsPlayerGame.id).filter(and_(StatsPlayerGame.game_id == game_id, StatsPlayerGame.player_id == player_id)).first() is not None


def normalize_stats_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a stats fixture into stats_player_game (idempotent by game_id+player_id).
    """
    session = get_session()

    league_code = str(payload.get("league") or "NBA")
    league = _get_or_create_league(session, league_code)

    games = payload.get("games") or []
    rows_created = 0
    rows_skipped = 0

    for g in games:
        external_id = str(g.get("external_id") or g.get("id") or "game_fixture")
        commence_time = str(g.get("commence_time") or "2026-02-20T09:00:00Z")
        home_team = str(g.get("home_team") or "HOME")
        away_team = str(g.get("away_team") or "AWAY")

        y0, y1 = _infer_season_from_commence(commence_time)
        season = _get_or_create_season(session, league.id, y0, y1)

        game = _get_or_create_game(session, external_id, league.id, season.id, commence_time, home_team, away_team)

        for pl in (g.get("players") or []):
            name = str(pl.get("player") or "").strip()
            if not name:
                continue
            player = _get_or_create_player(session, name)

            if _stat_row_exists(session, game.id, player.id):
                rows_skipped += 1
                continue

            row = StatsPlayerGame(
                game_id=game.id,
                player_id=player.id,
                minutes=float(pl.get("minutes") or 0.0),
                points=int(pl.get("points") or 0),
                assists=int(pl.get("assists") or 0),
                rebounds=int(pl.get("rebounds") or 0),
                threes_made=None,
                usage=None,
                ortg=None,
                drtg=None,
                ts_pct=None,
                pace=None,
            )
            session.add(row)
            rows_created += 1

    session.commit()
    return {"stats_created": rows_created, "stats_skipped_duplicates": rows_skipped, "league": league_code}
