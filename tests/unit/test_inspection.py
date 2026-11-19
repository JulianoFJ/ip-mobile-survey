import io
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string
from pydantic import ValidationError
from typer.testing import CliRunner

from ipsurvey.adapters.export.xlsx import SHEET_DATA, SHEET_SOURCE, XlsxInspectionSheetWriter
from ipsurvey.application.use_cases.export_inspection import ExportInspection
from ipsurvey.cli.main import app
from ipsurvey.domain.errors import DataValidationError
from ipsurvey.domain.inspection import COLUMNS, Arrangement, InspectionPoint, Source

FIXTURE = Path(__file__).parents[1] / "fixtures" / "simulacoes_cabecalho_B_AW.json"


def make_point(label: str = "P-0001", **kw: object) -> InspectionPoint:
    base: dict[str, object] = {
        "label": label,
        "latitude": -19.92,
        "longitude": -43.94,
        "street": "Rua Exemplo",
        "lanes": 2,
        "road_1_m": 7.0,
        "sidewalk_1_m": 2.0,
        "arrangement": "Unilateral",
        "structure_type": "Braço",
        "pole_spacing_m": 35.0,
        "luminaire_height_m": 9.2,
        "arm_projection_m": 1.8,
        "luminaires_main": 1,
        "confidence": {"luminaire_height_m": 0.95, "arm_projection_m": 0.5},
    }
    base.update(kw)
    return InspectionPoint.model_validate(base)


# ---------------------------------------------------------------- contrato
def test_columns_match_simulation_sheet() -> None:
    """Letras, cabeçalhos e colunas de fórmula idênticos à planilha de simulação."""
    ref = json.loads(FIXTURE.read_text(encoding="utf-8"))["colunas"]
    assert [c.letter for c in COLUMNS] == list(ref)
    assert [c.header for c in COLUMNS] == [v["header"] for v in ref.values()]
    formulas = {k for k, v in ref.items() if v["formula"]}
    assert {c.letter for c in COLUMNS if c.source is Source.SHEET} == formulas
    assert all(c.field is None for c in COLUMNS if c.source is Source.SHEET)


def test_columns_contiguous_b_to_aw() -> None:
    idx = [column_index_from_string(c.letter) for c in COLUMNS]
    assert idx == list(range(2, 2 + len(COLUMNS)))
    assert COLUMNS[-1].letter == "AW"


# ---------------------------------------------------------------- modelo
def test_point_row_uses_letters() -> None:
    row = make_point().to_row()
    assert row["E"] == "P-0001"
    assert row["AD"] == "Unilateral"
    assert row["AG"] == 9.2
    assert "Q" not in row  # fórmula
    assert row["B"] is None


def test_source_defaults_and_override() -> None:
    p = make_point(sources={"street": "levantamento"})
    assert p.source_of("street") is Source.SURVEY
    assert p.source_of("lamp_type") is Source.CADASTRE
    assert p.source_of("road_class") is Source.OFFICE


def test_low_confidence_fields() -> None:
    assert make_point().low_confidence_fields() == ["arm_projection_m"]


@pytest.mark.parametrize(
    "kw",
    [
        {"road_class": "M7"},
        {"pedestrian_class": "P9"},
        {"arrangement": "Lateral"},
        {"luminaire_height_m": -1},
        {"latitude": 95},
        {"confidence": {"campo_inexistente": 0.5}},
        {"arrangement": Arrangement.MEDIAN},  # exige canteiro central
    ],
)
def test_invalid_points(kw: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        make_point(**kw)


# ---------------------------------------------------------------- exportação
def test_xlsx_roundtrip() -> None:
    buf = io.BytesIO()
    n = ExportInspection(XlsxInspectionSheetWriter())(
        [make_point("P-0002"), make_point("P-0001", road_class="M3")], buf
    )
    assert n == 2
    wb = load_workbook(io.BytesIO(buf.getvalue()))
    ws = wb[SHEET_DATA]
    assert [ws[f"{c.letter}1"].value for c in COLUMNS] == [c.header for c in COLUMNS]
    assert ws["E2"].value == "P-0001"  # ordenado pela etiqueta
    assert ws["J2"].value == "M3"
    assert ws["AJ2"].fill.fgColor.rgb.endswith("FFF2CC")  # baixa confiança destacada
    assert ws["Q2"].value is None  # fórmula não preenchida
    assert wb[SHEET_SOURCE]["AG2"].value == "levantamento (0.95)"
    assert wb[SHEET_SOURCE]["G2"].value == "cadastro"


def test_duplicate_labels_rejected() -> None:
    with pytest.raises(DataValidationError, match="repetidas"):
        ExportInspection(XlsxInspectionSheetWriter())(
            [make_point("A"), make_point("A")], io.BytesIO()
        )


def test_cli_export(tmp_path: Path) -> None:
    src = tmp_path / "pontos.json"
    src.write_text(json.dumps([make_point().model_dump(mode="json")]), encoding="utf-8")
    out = tmp_path / "inspecao.xlsx"
    result = CliRunner().invoke(app, ["exportar-planilha", str(src), str(out)])
    assert result.exit_code == 0, result.output
    assert load_workbook(out)[SHEET_DATA]["E2"].value == "P-0001"


def test_cli_rejects_bad_data(tmp_path: Path) -> None:
    src = tmp_path / "pontos.json"
    src.write_text(json.dumps([{"label": "x"}]), encoding="utf-8")
    result = CliRunner().invoke(app, ["exportar-planilha", str(src), str(tmp_path / "o.xlsx")])
    assert result.exit_code == 2
