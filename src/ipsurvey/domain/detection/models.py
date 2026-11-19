"""Detecções de estruturas de IP: em pixels de uma vista e em ângulos do panorama."""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ipsurvey.domain.geometry.perspective import PerspectiveView


class StructureClass(StrEnum):
    """Estruturas detectadas."""

    POLE = "poste"
    ARM = "braco"
    LUMINAIRE = "luminaria"


@dataclass(frozen=True, slots=True)
class BoxPx:
    """Caixa em pixels contínuos de uma imagem (x para a direita, y para baixo)."""

    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        """Valida a orientação da caixa."""
        if not (self.x1 > self.x0 and self.y1 > self.y0):
            msg = f"caixa degenerada: {self}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Detection2D:
    """Saída de um detector numa imagem plana."""

    cls: StructureClass
    score: float
    box: BoxPx

    def __post_init__(self) -> None:
        """Valida o score."""
        if not 0.0 <= self.score <= 1.0:
            msg = f"score deve estar em [0, 1], recebido {self.score}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class AngularDetection:
    """Detecção no referencial do panorama (radianos).

    Attributes:
        cls: Estrutura.
        score: Confiança do detector, em [0, 1].
        az_center: Azimute do centro, em [-π, π).
        az_half_width: Meia largura angular (≥ 0). O intervalo pode atravessar ±π.
        el_min: Elevação da base (para o poste, o pé).
        el_max: Elevação do topo (para o poste, o topo).
        cut_bottom: A base encostava na borda da vista: o pé pode estar cortado.
        cut_top: O topo encostava na borda da vista.
        cut_side: Um dos lados encostava na borda da vista.
        views: Índices das vistas que contribuíram.
    """

    cls: StructureClass
    score: float
    az_center: float
    az_half_width: float
    el_min: float
    el_max: float
    cut_bottom: bool = False
    cut_top: bool = False
    cut_side: bool = False
    views: tuple[int, ...] = ()

    @property
    def truncated(self) -> bool:
        """Alguma borda foi cortada pela vista."""
        return self.cut_bottom or self.cut_top or self.cut_side

    @property
    def az_width(self) -> float:
        """Largura angular total (rad)."""
        return 2.0 * self.az_half_width

    def az_overlap(self, other: "AngularDetection") -> float:
        """Sobreposição em azimute, como fração da detecção mais estreita (0 a 1)."""
        d = abs(math.remainder(self.az_center - other.az_center, 2.0 * math.pi))
        narrow = min(self.az_half_width, other.az_half_width)
        inter = max(0.0, min(self.az_half_width + other.az_half_width - d, 2.0 * narrow))
        return inter / (2.0 * narrow) if narrow > 0 else 0.0

    def el_overlap(self, other: "AngularDetection") -> float:
        """Sobreposição em elevação (rad); negativa se houver espaço entre as duas."""
        return min(self.el_max, other.el_max) - max(self.el_min, other.el_min)


def to_angular(
    det: Detection2D,
    view: PerspectiveView,
    *,
    view_index: int = 0,
    edge_margin_px: float = 4.0,
    samples_per_edge: int = 16,
) -> AngularDetection:
    """Converte uma detecção de uma vista plana para ângulos do panorama.

    A caixa não é um retângulo em (azimute, elevação), principalmente em vistas inclinadas.
    Por isso a borda da caixa é amostrada e a faixa angular é o envelope desses pontos.

    Args:
        det: Detecção em pixels da vista.
        view: Vista onde a detecção foi feita.
        view_index: Índice da vista, registrado na detecção.
        edge_margin_px: Distância à borda abaixo da qual o lado conta como cortado.
        samples_per_edge: Pontos amostrados por lado da caixa.
    """
    b = det.box
    t = np.linspace(0.0, 1.0, samples_per_edge)
    w, h = b.x1 - b.x0, b.y1 - b.y0
    xs = np.concatenate([b.x0 + t * w, np.full_like(t, b.x1), b.x1 - t * w, np.full_like(t, b.x0)])
    ys = np.concatenate([np.full_like(t, b.y0), b.y0 + t * h, np.full_like(t, b.y1), b.y1 - t * h])
    az, el = view.pixel_to_angles(xs, ys)
    az_c, _ = view.pixel_to_angles((b.x0 + b.x1) / 2.0, (b.y0 + b.y1) / 2.0)
    rel = np.remainder(az - float(az_c) + math.pi, 2.0 * math.pi) - math.pi
    lo, hi = float(rel.min()), float(rel.max())
    m = edge_margin_px
    return AngularDetection(
        cls=det.cls,
        score=det.score,
        az_center=math.remainder(float(az_c) + (lo + hi) / 2.0, 2.0 * math.pi),
        az_half_width=(hi - lo) / 2.0,
        el_min=float(el.min()),
        el_max=float(el.max()),
        cut_bottom=b.y1 >= view.height - m,
        cut_top=b.y0 <= m,
        cut_side=b.x0 <= m or b.x1 >= view.width - m,
        views=(view_index,),
    )


def merge_detections(
    detections: list[AngularDetection],
    *,
    az_overlap: float = 0.5,
    el_gap: float = math.radians(2.0),
) -> list[AngularDetection]:
    """Junta detecções do mesmo objeto vindas de vistas sobrepostas.

    Duas detecções da mesma classe são o mesmo objeto quando se sobrepõem em azimute (pelo
    menos `az_overlap` da mais estreita) e em elevação (ou ficam a menos de `el_gap`). Isso
    também junta os pedaços de um poste alto que nenhuma vista vê inteiro: a base vem do
    pedaço que vê o pé e o topo do pedaço que vê o alto.

    Limitação: postes alinhados no mesmo azimute (um atrás do outro) viram um só; a
    triangulação em vários quadros separa.

    Returns:
        Uma detecção por objeto, ordenada por azimute.
    """
    kept: list[AngularDetection] = []
    for cls in StructureClass:
        pending = sorted(
            (d for d in detections if d.cls is cls), key=lambda d: (d.cut_side, -d.score)
        )
        while pending:
            group = [pending.pop(0)]
            grew = True
            while grew:  # junta por transitividade: pé ↔ meio ↔ topo
                grew = False
                for d in list(pending):
                    if any(
                        g.az_overlap(d) >= az_overlap and g.el_overlap(d) >= -el_gap for g in group
                    ):
                        group.append(d)
                        pending.remove(d)
                        grew = True
            kept.append(_union(group))
    return sorted(kept, key=lambda d: (d.az_center, d.cls))


def _union(group: list[AngularDetection]) -> AngularDetection:
    best = group[0]  # lados inteiros e maior score: define o azimute
    low = min(group, key=lambda d: (d.el_min, d.cut_bottom))
    high = max(group, key=lambda d: (d.el_max, not d.cut_top))
    return AngularDetection(
        cls=best.cls,
        score=max(d.score for d in group),
        az_center=best.az_center,
        az_half_width=best.az_half_width,
        el_min=low.el_min,
        el_max=high.el_max,
        cut_bottom=low.cut_bottom,
        cut_top=high.cut_top,
        cut_side=best.cut_side,
        views=tuple(sorted({v for d in group for v in d.views})),
    )
