from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from btb.db.connection import get_session
from btb.db.schema import Book, Game, League, OddsMarket, Season, Team


def _get_or_create_team(session, name: str, abbr: Optional[str] = None, external_id: Optional[str] = None) -> Team:
    team = session.query(Team).filter(Team.name == name).first()
    if team:
        return team
    team = Team(name=name, abbreviation=abbr, external_id=external_id)
    session.add(team)
    session.flush()
    return team


def _get_or_create_league_season(session, league_code: str, year_start: int, year_end: int) -> tuple[League, Season]:
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


def _get_or_create_book(session, code: str, name: str) -> Book:
    book = session.query(Book).filter(Book.code == code).first()
    if book:
        return book
    book = Book(code=code, name=name, is_aussie=False, sharp_flag=False)
    session.add(book)
    session.flush()
    return book


def normalize_the_odds_api_odds(payload: list[dict[str, Any]], league_code: str = "NBA") -> dict[str, Any]:
    """
    Normalize The Odds API odds payload into:
    - teams
    - games
    - books
    - odds_markets
    """
    session = get_session()

    games_created = 0
    markets_created = 0
    books_seen: set[str] = set()

    for event in payload:
        commence = event.get("commence_time")
        if not commence:
            continue

        commence_dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
        year = commence_dt.year
        year_start = year if commence_dt.month >= 10 else year - 1
        year_end = year_start + 1

        league, season = _get_or_create_league_season(session, league_code, year_start, year_end)

        home_name = event.get("home_team") or "HOME"
        away_name = event.get("away_team") or "AWAY"
        home = _get_or_create_team(session, home_name)
        away = _get_or_create_team(session, away_name)

        game_date = commence_dt.date()
        external_id = event.get("id")

        game = session.query(Game).filter(Game.external_id == external_id).first() if external_id else None
        if not game:
            game = Game(
                external_id=external_id,
                league_id=league.id,
                season_id=season.id,
                game_date=game_date,
                home_team_id=home.id,
                away_team_id=away.id,
                season_type="regular",
            )
            session.add(game)
            session.flush()
            games_created += 1

        for bookmaker in event.get("bookmakers", []) or []:
            book_key = bookmaker.get("key") or bookmaker.get("title") or "unknown"
            book_title = bookmaker.get("title") or bookmaker.get("key") or "Unknown"
            book = _get_or_create_book(session, code=book_key, name=book_title)
            books_seen.add(book.code)

            for market in bookmaker.get("markets", []) or []:
                mkey = market.get("key")  # h2h / spreads / totals

                for outcome in market.get("outcomes", []) or []:
                    if mkey == "h2h":
                        market_type = "moneyline"
                        out_name = outcome.get("name")
                        if out_name == home_name:
                            outcome_code = "home"
                        elif out_name == away_name:
                            outcome_code = "away"
                        else:
                            continue
                        line = None

                    elif mkey == "spreads":
                        market_type = "spread"
                        out_name = outcome.get("name")
                        if out_name == home_name:
                            outcome_code = "home"
                        elif out_name == away_name:
                            outcome_code = "away"
                        else:
                            continue
                        line = outcome.get("point")

                    elif mkey == "totals":
                        market_type = "total"
                        out_name = str(outcome.get("name") or "").lower()
                        if out_name == "over":
                            outcome_code = "over"
                        elif out_name == "under":
                            outcome_code = "under"
                        else:
                            continue
                        line = outcome.get("point")

                    else:
                        continue

                    price = outcome.get("price")
                    if price is None:
                        continue

                    row = OddsMarket(
                        game_id=game.id,
                        book_id=book.id,
                        market_type=market_type,
                        outcome=outcome_code,
                        line=line,
                        price=float(price),
                        source="the_odds_api",
                    )
                    session.add(row)
                    markets_created += 1

    session.commit()

    return {
        "games_created": games_created,
        "markets_created": markets_created,
        "books_seen": sorted(list(books_seen)),
    }
