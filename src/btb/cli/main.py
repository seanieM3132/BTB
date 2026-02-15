from __future__ import annotations

import typer

from btb.cli import phase1_research
from btb.db.connection import get_engine
from btb.db.schema import Base

app = typer.Typer(help="BTB CLI", add_completion=False)

app.add_typer(phase1_research.app, name="phase1")


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """BTB command line interface."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("version")
def version() -> None:
    """Print BTB version."""
    typer.echo("btb 0.1.0")


@app.command("init-db")
def init_db() -> None:
    """Initialize SQLite database and create tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    typer.echo("Database initialized.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
from btb.db.connection import get_session
from btb.db.schema import League, Book

@app.command("seed-core")
def seed_core() -> None:
    """Seed core reference data (league + basic books)."""
    session = get_session()

    # Add NBA league if not exists
    if not session.query(League).filter_by(code="NBA").first():
        session.add(League(code="NBA", name="National Basketball Association"))

    # Add basic books
    books = [
        ("sportsbet", "Sportsbet", True, False),
        ("tab", "TAB", True, False),
        ("pinnacle", "Pinnacle", False, True),
    ]

    for code, name, is_aussie, sharp_flag in books:
        if not session.query(Book).filter_by(code=code).first():
            session.add(Book(code=code, name=name, is_aussie=is_aussie, sharp_flag=sharp_flag))

    session.commit()
    typer.echo("Core data seeded.")
