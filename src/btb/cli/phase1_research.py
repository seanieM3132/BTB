from __future__ import annotations

import datetime
import typer

from btb.data_sources import odds_registry, props_registry
from btb.research import queries_props

app = typer.Typer(help="Phase 1: research backbone commands")


@app.command("ingest-odds")
def ingest_odds(
    league: str = typer.Argument("NBA"),
    date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
) -> None:
    """Ingest main market odds for a given date (provider fallbacks)."""
    target_date = datetime.date.fromisoformat(date)
    result = odds_registry.ingest_odds_with_fallbacks(league, target_date)
    typer.echo(result)


@app.command("ingest-odds-fixture")
def ingest_odds_fixture(
    path: str = typer.Argument(..., help="Path to The Odds API JSON fixture"),
    league: str = typer.Option("NBA", "--league"),
) -> None:
    """Ingest odds from a saved JSON fixture and normalize into DB."""
    result = odds_registry.ingest_odds_from_fixture(path, league=league)
    typer.echo(result)


@app.command("ingest-props-fixture")
def ingest_props_fixture(
    path: str = typer.Argument(..., help="Path to props JSON fixture"),
) -> None:
    """Ingest player props from a saved JSON fixture and normalize into DB."""
    result = props_registry.ingest_props_from_fixture(path)
    typer.echo(result)


@app.command("ingest-props")
def ingest_props(
    league: str = typer.Argument("NBA"),
    date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
) -> None:
    """Ingest player props for a given date (stub)."""
    _ = datetime.date.fromisoformat(date)
    typer.echo(f"[stub] ingest-props league={league} date={date}")


@app.command("ingest-stats")
def ingest_stats(
    league: str = typer.Argument("NBA"),
    season: str = typer.Option(..., "--season", help="e.g. 2024"),
) -> None:
    """Ingest season stats (stub)."""
    typer.echo(f"[stub] ingest-stats league={league} season={season}")


@app.command("ingest-playbyplay")
def ingest_playbyplay(
    league: str = typer.Argument("NBA"),
    season: str = typer.Option(..., "--season", help="e.g. 2024"),
) -> None:
    """Ingest play-by-play (stub)."""
    typer.echo(f"[stub] ingest-playbyplay league={league} season={season}")


@app.command("player-prop-research")
def player_prop_research(
    player_name: str = typer.Argument(...),
    game_date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
) -> None:
    """Print research bundle for a player's props on a date (v1 stub)."""
    target_date = datetime.date.fromisoformat(game_date)
    bundle = queries_props.get_player_prop_research(player_name, target_date)
    typer.echo(bundle)
