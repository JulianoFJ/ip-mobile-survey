"""Caso de uso: exportar a planilha de inspeção de uma campanha (P11, ADR 0006)."""

from collections.abc import Sequence
from typing import BinaryIO

from ipsurvey.application.ports import InspectionSheetWriter
from ipsurvey.domain.errors import DataValidationError
from ipsurvey.domain.inspection import InspectionPoint


class ExportInspection:
    """Gera a planilha de inspeção a partir dos pontos de IP levantados."""

    def __init__(self, writer: InspectionSheetWriter) -> None:
        """Recebe o escritor de planilha (porta)."""
        self._writer = writer

    def __call__(self, points: Sequence[InspectionPoint], dest: BinaryIO) -> int:
        """Exporta os pontos, ordenados pela etiqueta.

        Returns:
            Número de pontos exportados.

        Raises:
            DataValidationError: Se houver etiquetas repetidas (a planilha usa a etiqueta
                como chave do ponto).
        """
        labels = [p.label for p in points]
        dupes = sorted({x for x in labels if labels.count(x) > 1})
        if dupes:
            msg = f"etiquetas repetidas: {dupes[:10]}"
            raise DataValidationError(msg)
        ordered = sorted(points, key=lambda p: p.label)
        self._writer.write(ordered, dest)
        return len(ordered)
