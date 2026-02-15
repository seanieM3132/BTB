from __future__ import annotations

import typer

app = typer.Typer(help="BTB CLI", add_completion=False)

@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """BTB command line interface."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

@app.command("version")
def version() -> None:
    """Print BTB version."""
    typer.echo("btb 0.1.0")

def main() -> None:
    app()

if __name__ == "__main__":
    main()
