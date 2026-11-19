"""CLI `ipsurvey` (Typer)."""

import typer

from ipsurvey import PIPELINE_VERSION

app = typer.Typer(help="Levantamento móvel de ativos de IP.", no_args_is_help=True)


@app.command()
def version() -> None:
    """Mostra a versão do pipeline."""
    typer.echo(PIPELINE_VERSION)


@app.command()
def ingest(path: str, campaign: str) -> None:
    """Ingere uma captura bruta (P0). A implementar na S2."""
    typer.echo(f"[pendente S2] ingest {path} → campanha {campaign}")
    raise typer.Exit(code=1)
