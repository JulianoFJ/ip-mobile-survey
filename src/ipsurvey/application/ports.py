"""Portas (interfaces) da aplicação. Implementações concretas ficam em `adapters/`."""

from collections.abc import Iterable, Sequence
from typing import BinaryIO, Protocol
from uuid import UUID

import numpy as np
from numpy.typing import NDArray

from ipsurvey.domain.detection import Detection2D
from ipsurvey.domain.inspection import InspectionPoint
from ipsurvey.domain.models import Capture, PoleObservation


class ObjectStore(Protocol):
    """Armazenamento de objetos (S3/MinIO)."""

    def put(self, uri: str, data: BinaryIO) -> str:
        """Grava `data` em `uri` e devolve o SHA-256 do conteúdo."""
        ...

    def get(self, uri: str) -> BinaryIO:
        """Abre o objeto em `uri` para leitura."""
        ...

    def exists(self, uri: str) -> bool:
        """Indica se o objeto existe."""
        ...


class CaptureRepository(Protocol):
    """Persistência de capturas."""

    def add(self, capture: Capture) -> None:
        """Registra uma captura (idempotente por `raw_sha256`)."""
        ...

    def get(self, capture_id: UUID) -> Capture | None:
        """Busca uma captura pelo id."""
        ...


class PoleRepository(Protocol):
    """Persistência de observações de postes."""

    def add_many(self, observations: Iterable[PoleObservation]) -> None:
        """Grava observações (idempotente por `id`)."""
        ...

    def by_segment(self, segment_id: UUID) -> list[PoleObservation]:
        """Lista as observações de um segmento."""
        ...


class InspectionSheetWriter(Protocol):
    """Gera a planilha de inspeção (colunas B–AW da aba Simulações, ADR 0006)."""

    def write(self, points: Sequence[InspectionPoint], dest: BinaryIO) -> None:
        """Escreve uma linha por ponto em `dest`."""
        ...


class Detector(Protocol):
    """Detector de estruturas de IP numa imagem plana (RGB, uint8, H × W × 3)."""

    def detect(self, image: NDArray[np.uint8]) -> list[Detection2D]:
        """Detecta postes, braços e luminárias na imagem."""
        ...
