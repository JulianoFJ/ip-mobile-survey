"""Aplicação FastAPI."""

from fastapi import FastAPI

from ipsurvey import PIPELINE_VERSION
from ipsurvey.bootstrap import build_container

container = build_container()

app = FastAPI(
    title="ipsurvey",
    version=PIPELINE_VERSION,
    description="Levantamento móvel de ativos de iluminação pública",
)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    """Verificação de vida do serviço."""
    return {"status": "ok", "version": PIPELINE_VERSION, "env": container.settings.env}
