from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))

    seasons: Mapped[list["Season"]] = relationship(back_populates="league")


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    year_start: Mapped[int] = mapped_column(Integer, index=True)
    year_end: Mapped[int] = mapped_column(Integer, index=True)

    league: Mapped["League"] = relationship(back_populates="seasons")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    abbreviation: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(128), index=True)
    position: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"), nullable=True, index=True)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)

    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)

    game_date: Mapped[date] = mapped_column(Date, index=True)

    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)

    season_type: Mapped[str] = mapped_column(String(16), default="regular")  # regular/playin/playoffs
    series_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    game_number_in_series: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_elimination_game: Mapped[bool] = mapped_column(Boolean, default=False)

    home_rest_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_rest_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    home_travel_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_travel_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    altitude_category: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # low/medium/high


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    is_aussie: Mapped[bool] = mapped_column(Boolean, default=False)
    sharp_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class OddsMarket(Base):
    __tablename__ = "odds_markets"
    __table_args__ = (
        UniqueConstraint("game_id", "book_id", "market_type", "outcome", "line", "collected_ts", name="uq_odds_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)

    market_type: Mapped[str] = mapped_column(String(16))  # moneyline/spread/total
    outcome: Mapped[str] = mapped_column(String(16))      # home/away/over/under
    line: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price: Mapped[float] = mapped_column(Float)

    collected_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class PropsMarket(Base):
    __tablename__ = "props_markets"
    __table_args__ = (
        UniqueConstraint("game_id", "player_id", "book_id", "prop_type", "line", "price", "collected_ts", name="uq_props_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)

    prop_type: Mapped[str] = mapped_column(String(32))  # points, assists, PRA, etc.
    line: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)

    collected_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    alt_line_group_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class RawProvider(Base):
    __tablename__ = "raw_provider"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    collected_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    scope: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # odds/props/stats/pbp


class Bet(Base):
    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    placed_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    game_id: Mapped[Optional[int]] = mapped_column(ForeignKey("games.id"), nullable=True, index=True)
    props_market_id: Mapped[Optional[int]] = mapped_column(ForeignKey("props_markets.id"), nullable=True, index=True)

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)

    stake: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)

    result: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # W/L/PUSH/VOID
    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class CLVObservation(Base):
    __tablename__ = "clv_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bet_id: Mapped[int] = mapped_column(ForeignKey("bets.id"), index=True)
    reference_book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)

    open_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    closing_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calculated_clv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class LimitsSnapshot(Base):
    __tablename__ = "limits_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    market_scope: Mapped[str] = mapped_column(String(64))  # e.g. nba_moneyline / player_points
    limit_amount: Mapped[float] = mapped_column(Float)
    effective_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PlayByPlayEvent(Base):
    __tablename__ = "play_by_play_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)

    event_index: Mapped[int] = mapped_column(Integer)
    period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clock: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id"), nullable=True, index=True)
    player_id_primary: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)
    player_id_secondary: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)

    event_type: Mapped[str] = mapped_column(String(32))
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    lineup_home_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lineup_away_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
