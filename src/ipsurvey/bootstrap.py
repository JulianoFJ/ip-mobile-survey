"""Composição de dependências: o ÚNICO lugar que liga portas a adaptadores."""

from dataclasses import dataclass

from ipsurvey.logging import configure_logging
from ipsurvey.settings import Settings, get_settings


@dataclass(frozen=True)
class Container:
    """Dependências resolvidas para um processo (API, CLI ou worker)."""

    settings: Settings


def build_container(settings: Settings | None = None) -> Container:
    """Monta o container e configura logs."""
    s = settings or get_settings()
    configure_logging(s.log_level, json=s.log_json)
    return Container(settings=s)
