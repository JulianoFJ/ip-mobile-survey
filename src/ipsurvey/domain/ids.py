"""Geração de identificadores (UUIDv7, ordenáveis por tempo)."""

from uuid import UUID

import uuid6


def new_id() -> UUID:
    """Gera um UUIDv7.

    Returns:
        UUID versão 7, ordenável pelo instante de criação.
    """
    return UUID(bytes=uuid6.uuid7().bytes)
