"""Entidades e value objects centrais (§6.2 da especificação).

Convenções: unidades SI, ângulos em radianos, tempo em UTC com timezone.
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from ipsurvey.domain.errors import CRSMismatchError

SCHEMA_VERSION = "0.1.0"


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        msg = "datetime deve ter timezone (UTC)"
        raise ValueError(msg)
    return value


def _require_epsg(value: str) -> str:
    prefix, _, code = value.partition(":")
    if prefix != "EPSG" or not code.isdigit():
        msg = f"CRS deve estar no formato 'EPSG:<código>', recebido {value!r}"
        raise ValueError(msg)
    return value


AwareDatetime = Annotated[datetime, AfterValidator(_require_utc)]
CRS = Annotated[str, AfterValidator(_require_epsg)]
Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Frozen(BaseModel):
    """Base imutável e estrita para entidades e value objects."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class ProjectedPoint(Frozen):
    """Ponto em CRS projetado (metros). O CRS acompanha sempre a coordenada (§19, item 3)."""

    x: float
    y: float
    z: float = 0.0
    crs: CRS

    def distance_xy(self, other: Self) -> float:
        """Distância horizontal até `other`, em metros.

        Raises:
            CRSMismatchError: Se os pontos estiverem em CRS diferentes.
        """
        if other.crs != self.crs:
            msg = f"{self.crs} != {other.crs}"
            raise CRSMismatchError(msg)
        return float(((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5)


class PoseENU(Frozen):
    """Pose do sensor num instante, em CRS projetado."""

    t: AwareDatetime
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
    sigma_xy: float = Field(ge=0, description="Incerteza 1σ horizontal (m)")
    sigma_z: float = Field(ge=0, description="Incerteza 1σ vertical (m)")
    rtk_fix: bool = False


class Capture(Frozen):
    """Uma captura bruta (imutável) de uma fonte de dados."""

    id: UUID
    campaign_id: UUID
    source: str
    sensor_profile: str
    crs: CRS
    started_at: AwareDatetime
    raw_uri: str
    raw_sha256: Sha256


class Segment(Frozen):
    """Trecho de ~500 m da trajetória: unidade de processamento."""

    id: UUID
    capture_id: UUID
    t_start: AwareDatetime
    t_end: AwareDatetime
    length_m: float = Field(gt=0)

    @model_validator(mode="after")
    def _check_interval(self) -> Self:
        if self.t_end <= self.t_start:
            msg = "t_end deve ser posterior a t_start"
            raise ValueError(msg)
        return self


class PoleObservation(Frozen):
    """O que a extração encontrou para um poste num segmento."""

    id: UUID
    segment_id: UUID
    position: ProjectedPoint
    height_m: float | None = Field(default=None, gt=0)
    tilt_rad: float | None = None
    arm_projection_m: float | None = Field(default=None, ge=0)
    arm_tilt_rad: float | None = None
    luminaire_family: str | None = None
    confidence: dict[str, Confidence] = Field(default_factory=dict)
    method: dict[str, str] = Field(default_factory=dict)
    evidence_uris: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _confidence_has_method(self) -> Self:
        missing = set(self.confidence) - set(self.method)
        if missing:
            msg = f"confiança sem método de origem para: {sorted(missing)}"
            raise ValueError(msg)
        return self


class ReviewStatus(StrEnum):
    """Estado de revisão humana de um item."""

    AUTO = "auto"
    PENDING = "pending"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"
    REJECTED = "rejected"
