"""Ponto de IP inspecionado: uma linha da planilha de inspeção (ADR 0006)."""

from enum import StrEnum
from typing import Annotated, Any, Self

from pydantic import Field, model_validator

from ipsurvey.domain.inspection.columns import COLUMNS, FIELD_COLUMNS, Source
from ipsurvey.domain.models.core import Confidence, Frozen

Meters = Annotated[float, Field(ge=0, le=200)]
Watts = Annotated[float, Field(ge=0, le=5000)]
Count = Annotated[int, Field(ge=0, le=20)]
RoadClass = Annotated[str, Field(pattern=r"^(M[1-6]|C[0-5])$")]
PedestrianClass = Annotated[str, Field(pattern=r"^(P[1-6]|-)$")]


class Arrangement(StrEnum):
    """Posteação, com os valores aceitos pela planilha de simulação."""

    UNILATERAL = "Unilateral"
    BILATERAL_ALTERNATE = "Bilateral Alternada"
    BILATERAL_FRONT = "Bilateral Frontal"
    MEDIAN = "Canteiro Central"


class InspectionPoint(Frozen):
    """Um ponto de IP (poste com suas luminárias) e os atributos da planilha de inspeção.

    Unidades: metros e watts. Campos não levantados ficam `None` (célula vazia).
    `sources` e `confidence` são indexados pelo nome do campo.
    """

    cadastre_id: str | None = None
    simulate: str | None = None
    automated: str | None = None
    label: str
    pattern: str | None = None
    street: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    road_class: RoadClass | None = None
    cycle_class: str | None = None
    pedestrian_class: PedestrianClass | None = None
    lamp_type: str | None = None
    lamp_power_w: Watts | None = None
    ballast: str | None = None
    lamp_power_2nd_w: Watts | None = None
    lanes: Count | None = None
    sidewalk_1_m: Meters | None = None
    road_1_m: Meters | None = None
    central_sidewalk_1_m: Meters | None = None
    central_sidewalk_2_m: Meters | None = None
    road_2_m: Meters | None = None
    sidewalk_2_m: Meters | None = None
    median_m: Meters | None = None
    cycleway_1_m: Meters | None = None
    cycleway_2_m: Meters | None = None
    parking_1_m: Meters | None = None
    parking_2_m: Meters | None = None
    arrangement: Arrangement | None = None
    structure_type: str | None = None
    pole_spacing_m: Meters | None = None
    luminaire_height_m: Meters | None = None
    luminaires_main: Count | None = None
    pole_setback_m: Annotated[float, Field(ge=-20, le=50)] | None = None
    arm_projection_m: Meters | None = None
    mounting_height_m: Meters | None = None
    vertical_projection_m: Meters | None = None
    exclusive: str | None = None
    luminaires_2nd: Count | None = None
    arrangement_2nd: str | None = None
    spacing_2nd_m: Meters | None = None
    luminaire_height_2nd_m: Meters | None = None
    arm_projection_2nd_m: Meters | None = None
    pole_setback_2nd_m: Annotated[float, Field(ge=-20, le=50)] | None = None
    notes: str | None = None

    sources: dict[str, Source] = Field(default_factory=dict)
    confidence: dict[str, Confidence] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_metadata(self) -> Self:
        unknown = (set(self.sources) | set(self.confidence)) - set(FIELD_COLUMNS)
        if unknown:
            msg = f"metadados para campos inexistentes: {sorted(unknown)}"
            raise ValueError(msg)
        if self.arrangement is Arrangement.MEDIAN and not self.median_m:
            msg = "posteação 'Canteiro Central' exige largura do canteiro central"
            raise ValueError(msg)
        return self

    def source_of(self, field: str) -> Source:
        """Origem do campo: a declarada no ponto ou a padrão da coluna."""
        return self.sources.get(field, FIELD_COLUMNS[field].source)

    def low_confidence_fields(self, threshold: float = 0.7) -> list[str]:
        """Campos preenchidos com confiança abaixo de `threshold` (para revisão humana)."""
        return [
            f for f, c in self.confidence.items() if c < threshold and getattr(self, f) is not None
        ]

    def to_row(self) -> dict[str, Any]:
        """Valores por letra de coluna (B–AW); colunas de fórmula ficam fora."""
        row: dict[str, Any] = {}
        for col in COLUMNS:
            if col.field is None:
                continue
            value = getattr(self, col.field)
            row[col.letter] = value.value if isinstance(value, StrEnum) else value
        return row
