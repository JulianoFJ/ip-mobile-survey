"""Planilha de inspeção em .xlsx (openpyxl), nas letras da aba Simulações (ADR 0006).

Abas geradas:
    * **Inspeção:** cabeçalho na linha 1 e um ponto por linha, colunas B–AW, nas mesmas letras da
      aba Simulações, para copiar e colar sem ajuste. Colunas de fórmula ficam vazias (cinza).
    * **Origem:** para cada célula, a origem do valor e a confiança (quando medida).
    * **Legenda:** significado das cores.

Cores das células de dados: amarelo = baixa confiança (revisar); sem cor = ok.
"""

from collections.abc import Sequence
from typing import BinaryIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

from ipsurvey.domain.inspection import COLUMNS, InspectionPoint, Source

SHEET_DATA = "Inspeção"
SHEET_SOURCE = "Origem"
SHEET_LEGEND = "Legenda"

_LOW = PatternFill("solid", fgColor="FFF2CC")
_FORMULA = PatternFill("solid", fgColor="EDEDED")
_HEADER_FILL = {
    Source.SURVEY: PatternFill("solid", fgColor="DDEBF7"),
    Source.CADASTRE: PatternFill("solid", fgColor="E2EFDA"),
    Source.OFFICE: PatternFill("solid", fgColor="FCE4D6"),
    Source.SHEET: _FORMULA,
}


class XlsxInspectionSheetWriter:
    """Implementa `InspectionSheetWriter` com openpyxl."""

    def __init__(self, low_confidence: float = 0.7) -> None:
        """Cria o escritor.

        Args:
            low_confidence: Abaixo deste valor, a célula é destacada para revisão.
        """
        self._low = low_confidence

    def write(self, points: Sequence[InspectionPoint], dest: BinaryIO) -> None:
        """Escreve a planilha de inspeção em `dest` (.xlsx)."""
        wb = Workbook()
        data = wb.active
        assert data is not None
        data.title = SHEET_DATA
        origin = wb.create_sheet(SHEET_SOURCE)
        self._headers(data)
        self._headers(origin)
        for i, point in enumerate(points, start=2):
            self._row(data, origin, i, point)
        self._legend(wb.create_sheet(SHEET_LEGEND))
        wb.save(dest)

    @staticmethod
    def _headers(ws: Worksheet) -> None:
        for col in COLUMNS:
            cell = ws[f"{col.letter}1"]
            cell.value = col.header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.fill = _HEADER_FILL[col.source]
            ws.column_dimensions[col.letter].width = 14
        ws.row_dimensions[1].height = 60
        ws.freeze_panes = "F2"

    def _row(self, data: Worksheet, origin: Worksheet, r: int, point: InspectionPoint) -> None:
        values = point.to_row()
        low = set(point.low_confidence_fields(self._low))
        for col in COLUMNS:
            if col.field is None:
                data[f"{col.letter}{r}"].fill = _FORMULA
                continue
            data[f"{col.letter}{r}"] = values[col.letter]
            if col.field in low:
                data[f"{col.letter}{r}"].fill = _LOW
            if values[col.letter] is not None:
                src = point.source_of(col.field).value
                conf = point.confidence.get(col.field)
                origin[f"{col.letter}{r}"] = src if conf is None else f"{src} ({conf:.2f})"

    @staticmethod
    def _legend(ws: Worksheet) -> None:
        rows = [
            ("Cor", "Significado"),
            ("Azul (cabeçalho)", "Medido pelo levantamento móvel"),
            ("Verde (cabeçalho)", "Cadastro do município"),
            ("Laranja (cabeçalho)", "Classificação do escritório"),
            ("Cinza", "Fórmula da planilha de simulação: não preenchido"),
            ("Amarelo (célula)", "Baixa confiança: revisar antes de simular"),
        ]
        for i, (a, b) in enumerate(rows, start=1):
            ws[f"A{i}"], ws[f"B{i}"] = a, b
        ws["A1"].font = ws["B1"].font = Font(bold=True)
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 50
