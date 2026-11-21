"""Atributos de via e malha a partir de um panorama (postes e luminárias detectados).

Referencial local da câmera, no chão: x lateral (positivo à direita do sentido de
deslocamento), y longitudinal (positivo à frente). O sentido de deslocamento, em azimute
do panorama, é `travel_az`: a câmera nem sempre está com o centro da imagem para a
frente do veículo, então ele vem da trajetória (rumo entre fotos vizinhas menos o rumo
do centro da imagem). O chão é plano e a câmera está a `camera_height_m`.

O que sai daqui alimenta a planilha de simulação:

* AD posteação: lados com poste e alinhamento entre os dois lados;
* AF distância entre postes: mediana dos espaçamentos longitudinais no mesmo lado;
* AL/AG altura de instalação e da luminária: luminária associada ao poste vizinho;
* AJ projeção do braço: distância lateral entre o poste e a luminária;
* largura entre alinhamentos de postes: limite superior de passeio + via + passeio.

As larguras de pista, passeio e canteiro (S–Y) dependem da segmentação da superfície e
não saem daqui.

Hipóteses de geometria (documentadas porque erram em casos conhecidos):

* luminária no plano perpendicular à via que passa pelo poste (braço transversal);
* poste no lado em que o pé aparece; poste no canteiro central quando está a menos de
  `median_max_offset_m` do eixo do veículo e há postes dos dois lados ou só ele.
"""

import itertools
import math
import statistics
from dataclasses import dataclass, replace
from enum import StrEnum

from ipsurvey.domain.detection.ground import ground_estimate
from ipsurvey.domain.detection.models import AngularDetection, StructureClass


class Side(StrEnum):
    """Lado da via em relação ao sentido de deslocamento."""

    LEFT = "esquerda"
    RIGHT = "direita"
    CENTER = "centro"


@dataclass(frozen=True, slots=True)
class PolePlan:
    """Poste projetado no chão."""

    index: int
    x_m: float
    y_m: float
    height_m: float
    height_is_lower_bound: bool
    side: Side


@dataclass(frozen=True, slots=True)
class LuminaireFix:
    """Luminária associada a um poste."""

    pole_index: int
    mounting_height_m: float
    arm_projection_m: float


@dataclass(frozen=True, slots=True)
class RoadEstimate:
    """Atributos de via e malha de um panorama. `None` quando não há base para estimar."""

    poles: tuple[PolePlan, ...]
    luminaires: tuple[LuminaireFix, ...]
    arrangement: str | None
    pole_spacing_m: float | None
    spacing_samples: int
    alignment_width_m: float | None
    mounting_height_m: float | None
    arm_projection_m: float | None


def plan_poles(
    dets: list[AngularDetection],
    camera_height_m: float,
    *,
    median_max_offset_m: float = 2.5,
) -> list[PolePlan]:
    """Projeta no chão os postes com pé visível."""
    out: list[PolePlan] = []
    for i, d in enumerate(dets):
        if d.cls is not StructureClass.POLE:
            continue
        est = ground_estimate(d, camera_height_m)
        if est is None:
            continue
        x = est.distance_m * math.sin(d.az_center)
        y = est.distance_m * math.cos(d.az_center)
        side = Side.CENTER if abs(x) < median_max_offset_m else Side.RIGHT if x > 0 else Side.LEFT
        out.append(PolePlan(i, x, y, est.height_m, est.height_is_lower_bound, side))
    return out


def pole_spacing(
    poles: list[PolePlan],
    *,
    min_m: float = 8.0,
    max_m: float = 70.0,
    same_line_m: float = 2.5,
) -> tuple[float | None, int]:
    """Mediana dos espaçamentos longitudinais entre postes vizinhos do mesmo alinhamento.

    Dois postes estão no mesmo alinhamento quando estão do mesmo lado e com afastamento
    lateral parecido (até `same_line_m`). Espaçamentos fora de [min_m, max_m] são
    descartados: abaixo, costuma ser poste duplicado ou de outra rede; acima, um poste
    no meio que não foi detectado.

    Returns:
        (mediana em metros ou None, número de espaçamentos usados).
    """
    gaps: list[float] = []
    for side in Side:
        line = sorted((p for p in poles if p.side is side), key=lambda p: p.y_m)
        for a, b in itertools.pairwise(line):
            dy = b.y_m - a.y_m
            if abs(b.x_m - a.x_m) <= same_line_m and min_m <= dy <= max_m:
                gaps.append(dy)
    return (statistics.median(gaps), len(gaps)) if gaps else (None, 0)


def arrangement(
    poles: list[PolePlan], spacing_m: float | None, *, front_tol: float = 0.25
) -> str | None:
    """Posteação no vocabulário da planilha de simulação.

    Bilateral frontal quando os postes dos dois lados ficam frente a frente (diferença
    longitudinal até `front_tol` do espaçamento, ou 5 m sem espaçamento conhecido).
    """
    sides = {p.side for p in poles}
    if not poles:
        return None
    if sides == {Side.CENTER}:
        return "Canteiro Central"
    left = [p for p in poles if p.side is Side.LEFT]
    right = [p for p in poles if p.side is Side.RIGHT]
    if not left or not right:
        return "Canteiro Central" if Side.CENTER in sides else "Unilateral"
    tol = front_tol * spacing_m if spacing_m else 5.0
    paired = sum(1 for p in left if any(abs(p.y_m - q.y_m) <= tol for q in right))
    return "Bilateral Frontal" if paired >= max(1, len(left) // 2) else "Bilateral Alternada"


def alignment_width(poles: list[PolePlan], *, max_along_m: float = 30.0) -> float | None:
    """Distância lateral entre os alinhamentos de postes da esquerda e da direita.

    Só usa postes a até `max_along_m` à frente ou atrás: mais longe, a via pode ter
    mudado (cruzamento, curva) e o poste do outro lado já não é do mesmo trecho.
    """
    perto = [p for p in poles if abs(p.y_m) <= max_along_m]
    left = [p.x_m for p in perto if p.side is Side.LEFT]
    right = [p.x_m for p in perto if p.side is Side.RIGHT]
    if not left or not right:
        return None
    return statistics.median(right) - statistics.median(left)


def fix_luminaires(  # noqa: PLR0913 (limiares nomeados, só keyword)
    dets: list[AngularDetection],
    poles: list[PolePlan],
    camera_height_m: float,
    *,
    min_cos: float = 0.25,
    max_arm_m: float = 6.0,
    min_rel_height: float = 0.6,
    top_margin_m: float = 1.5,
) -> list[LuminaireFix]:
    """Associa cada luminária a um poste e mede a altura de instalação e o braço.

    A luminária fica no plano perpendicular à via que passa pelo poste (y_l = y_p), então
    o azimute dela dá x_l = y_p · tan(az_l). Sem solução estável quando o poste está quase
    ao lado da câmera (|cos az| < `min_cos`): esses ficam de fora.

    Um poste só aceita a luminária se o resultado for fisicamente coerente: braço até
    `max_arm_m` e altura entre `min_rel_height` da altura do poste e o topo mais
    `top_margin_m` (sem teto quando o topo do poste foi cortado). Isso descarta semáforos,
    placas e luzes de fachada que caem perto do poste em azimute. Entre os postes que
    aceitam, fica o mais próximo em azimute.
    """
    out: list[LuminaireFix] = []
    for lum in dets:
        if lum.cls is not StructureClass.LUMINAIRE:
            continue
        cos_az = math.cos(lum.az_center)
        if abs(cos_az) < min_cos:
            continue
        el_c = (lum.el_min + lum.el_max) / 2.0
        best: tuple[float, LuminaireFix] | None = None
        for p in poles:
            if (cos_az > 0) != (p.y_m > 0) or (p.side is Side.CENTER and abs(p.x_m) < 0.5):
                continue
            gap = abs(math.remainder(lum.az_center - dets[p.index].az_center, 2.0 * math.pi))
            if gap > math.atan2(max_arm_m, math.hypot(p.x_m, p.y_m)) + dets[p.index].az_half_width:
                continue
            x_l = p.y_m * math.tan(lum.az_center)
            arm = abs(x_l - p.x_m)
            h = camera_height_m + math.hypot(x_l, p.y_m) * math.tan(el_c)
            teto = math.inf if p.height_is_lower_bound else p.height_m + top_margin_m
            if arm > max_arm_m or not min_rel_height * p.height_m <= h <= teto:
                continue
            if best is None or gap < best[0]:
                best = (gap, LuminaireFix(p.index, h, arm))
        if best is not None:
            out.append(best[1])
    return out


def estimate_road(
    dets: list[AngularDetection], camera_height_m: float, travel_az: float = 0.0
) -> RoadEstimate:
    """Todos os atributos de via e malha que um panorama permite estimar.

    Args:
        dets: Detecções do panorama (os índices de `PolePlan.index` apontam para esta lista).
        camera_height_m: Altura da câmera sobre o chão.
        travel_az: Azimute do panorama (rad) que aponta no sentido de deslocamento.
    """
    if travel_az:
        dets = [
            replace(d, az_center=math.remainder(d.az_center - travel_az, 2.0 * math.pi))
            for d in dets
        ]
    poles = plan_poles(dets, camera_height_m)
    spacing, n = pole_spacing(poles)
    lums = fix_luminaires(dets, poles, camera_height_m)
    return RoadEstimate(
        poles=tuple(poles),
        luminaires=tuple(lums),
        arrangement=arrangement(poles, spacing),
        pole_spacing_m=spacing,
        spacing_samples=n,
        alignment_width_m=alignment_width(poles),
        mounting_height_m=statistics.median(lf.mounting_height_m for lf in lums) if lums else None,
        arm_projection_m=statistics.median(lf.arm_projection_m for lf in lums) if lums else None,
    )
