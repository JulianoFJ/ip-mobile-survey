"""CLI `ipsurvey` (Typer)."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from ipsurvey import PIPELINE_VERSION
from ipsurvey.bootstrap import build_container
from ipsurvey.domain.errors import DataValidationError
from ipsurvey.domain.inspection import InspectionPoint

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


@app.command("exportar-planilha")
def export_sheet(
    pontos: Annotated[Path, typer.Argument(help="JSON com a lista de pontos de IP", exists=True)],
    saida: Annotated[Path, typer.Argument(help="Arquivo .xlsx de saída")],
) -> None:
    """Gera a planilha de inspeção (colunas B–AW da aba Simulações)."""
    try:
        raw = json.loads(pontos.read_text(encoding="utf-8"))
        points = [InspectionPoint.model_validate(p) for p in raw]
        with saida.open("wb") as f:
            n = build_container().export_inspection(points, f)
    except (ValidationError, DataValidationError, json.JSONDecodeError) as e:
        typer.echo(f"Erro nos dados: {e}", err=True)
        raise typer.Exit(code=2) from e
    typer.echo(f"{n} pontos exportados para {saida}")
