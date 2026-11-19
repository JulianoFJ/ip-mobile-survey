"""Logs estruturados (structlog) com rastreio por `run_id`."""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", *, json: bool = False) -> None:
    """Configura structlog para todo o processo.

    Args:
        level: Nível mínimo (DEBUG, INFO, WARNING...).
        json: True emite JSON (nuvem); False emite texto colorido (local).
    """
    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[*processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        logger_factory=structlog.PrintLoggerFactory(sys.stderr),
        cache_logger_on_first_use=True,
    )


def bind_run(run_id: str, **fields: object) -> None:
    """Associa `run_id` (e outros campos) a todos os logs do contexto atual."""
    structlog.contextvars.bind_contextvars(run_id=run_id, **fields)
