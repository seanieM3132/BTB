from __future__ import annotations

import datetime
import typer

from btb.research import queries_props
from btb.research.reports_explain import render_prop_report
from btb.data_sources import odds_registry, props_registry, stats_registry

app = typer.Typer(help="Phase 1: research backbone commands")


@app.command("ingest-odds")
def ingest_odds(
    league: str = typer.Argument("NBA"),
    date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
) -> None:
    target_date = datetime.date.fromisoformat(date)
    result = odds_registry.ingest_day_main_markets(league, target_date)
    typer.echo(result)


@app.command("ingest-odds-fixture")
def ingest_odds_fixture(
    path: str = typer.Argument(..., help="Path to odds JSON fixture"),
    league: str = typer.Option("NBA", "--league"),
) -> None:
    result = odds_registry.ingest_odds_from_fixture(path, league=league)
    typer.echo(result)


@app.command("ingest-props-fixture")
def ingest_props_fixture(
    path: str = typer.Argument(..., help="Path to props JSON fixture"),
) -> None:
    result = props_registry.ingest_props_from_fixture(path)
    typer.echo(result)


@app.command("ingest-stats-fixture")
def ingest_stats_fixture(
    path: str = typer.Argument(..., help="Path to stats JSON fixture"),
) -> None:
    result = stats_registry.ingest_stats_from_fixture(path)
    typer.echo(result)


@app.command("player-prop-research")
def player_prop_research(
    player_name: str = typer.Argument(...),
    game_date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
) -> None:
    target_date = datetime.date.fromisoformat(game_date)
    bundle = queries_props.get_player_prop_research(player_name, target_date)
    typer.echo(bundle)


@app.command("report-prop")
def report_prop(
    player_name: str = typer.Argument(...),
    game_date: str = typer.Option(..., "--date", help="YYYY-MM-DD"),
) -> None:
    target_date = datetime.date.fromisoformat(game_date)
    bundle = queries_props.get_player_prop_research(player_name, target_date)
    report = render_prop_report(bundle)
    typer.echo(report)
