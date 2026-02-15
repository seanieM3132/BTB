from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from btb.db.connection import get_session
from btb.db.schema import Book, Game, League, Player, PropsMarket, Season, Team


def _get_or_create_book(session, code: str, name: str) -> Book:
    book = session.query(Book).filter(Book.code == code).first()
    if book:
        return book
    book = Book(code=code, name=name, is_aussie=False, sharp_flag=False)
    session.add(book)
    session.flush()
    return book


def _get_or_create_team(session, name: str) -> Team:
    team = session.query(Team).filter(Team.name == name).first()
    if team:
        return team
    team = Team(name=name, abbreviation=None, external_id=None)
    session.add(team)
    session.flush()
    return team


def _get_or_create_league_season(session, league_code: str, commence_time: str) -> tuple[League, Season]:
    commence_dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
    year = commence_dt.year
    year_start = year if commence_dt.month >= 10 else year - 1
    year_end = year_start + 1

    league = session.query(League).filter(League.code == league_code).first()
    if not league:
        league = League(code=league_code, name=league_code)
        session.add(league)
        session.flush()

    season = (
        session.query(Season)
        .filter(Season.league_id == league.id, Season.year_start == year_start, Season.year_end == year_end)
        .first()
    )
    if not season:
        season = Season(league_id=league.id, year_start=year_start, year_end=year_end)
        session.add(season)
        session.flush()

    return league, season


def _get_or_create_game(
    session,
    external_id: str,
    home_team: str,
    away_team: str,
    commence_time: str,
    league_code: str = "NBA",
) -> Game:
    game = session.query(Game).filter(Game.external_id == external_id).first()
    if game:
        return game

    commence_dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
    league, season = _get_or_create_league_season(session, league_code, commence_time)

    home = _get_or_create_team(session, home_team)
    away = _get_or_create_team(session, away_team)

    game = Game(
        external_id=external_id,
        league_id=league.id,
        season_id=season.id,
        game_date=commence_dt.date(),
        home_team_id=home.id,
        away_team_id=away.id,
        season_type="regular",
    )
    session.add(game)
    session.flush()
    return game


def _get_or_create_player(session, full_name: str, external_id: Optional[str] = None, team_id: Optional[int] = None) -> Player:
    player = session.query(Player).filter(Player.full_name == full_name).first()
    if player:
        return player
    player = Player(full_name=full_name, external_id=external_id, position=None, team_id=team_id)
    session.add(player)
    session.flush()
    return player


def normalize_props_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a generic props fixture payload into PropsMarket rows.

    Expected fixture structure (minimal):
    {
      "game": {"id": "...", "commence_time":"...Z", "home_team":"...", "away_team":"..."},
      "book": {"key":"sportsbet","title":"Sportsbet"},
      "league": "NBA",
      "props": [
        {"player":"Jayson Tatum","prop_type":"points","line":28.5,"price":1.90},
        ...
      ]
    }
    """
    session = get_session()

    league_code = str(payload.get("league") or "NBA")

    game_obj = payload.get("game") or {}
    book_obj = payload.get("book") or {}
    props = payload.get("props") or []

    game_external_id = str(game_obj.get("id") or "game_fixture")
    commence_time = str(game_obj.get("commence_time") or "2026-02-20T09:00:00Z")
    home_team = str(game_obj.get("home_team") or "HOME")
    away_team = str(game_obj.get("away_team") or "AWAY")

    game = _get_or_create_game(session, game_external_id, home_team, away_team, commence_time, league_code=league_code)
    book = _get_or_create_book(session, str(book_obj.get("key") or "unknown"), str(book_obj.get("title") or "Unknown"))

    rows_created = 0
    players_seen: set[str] = set()

    for p in props:
        player_name = str(p.get("player") or "").strip()
        if not player_name:
            continue
        prop_type = str(p.get("prop_type") or "").strip().lower()
        if not prop_type:
            continue
        line = p.get("line")
        price = p.get("price")
        if line is None or price is None:
            continue

        player = _get_or_create_player(session, player_name)
        players_seen.add(player.full_name)

        row = PropsMarket(
            game_id=game.id,
            player_id=player.id,
            book_id=book.id,
            prop_type=prop_type,
            line=float(line),
            price=float(price),
            source="fixture",
        )
        session.add(row)
        rows_created += 1

    session.commit()

    return {
        "props_created": rows_created,
        "players_seen": sorted(list(players_seen)),
        "book": book.code,
        "game_external_id": game.external_id,
        "league": league_code,
    }
