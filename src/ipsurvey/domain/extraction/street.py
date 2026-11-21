"""Distância entre postes e posteação de uma rua, a partir dos postes do cadastro.

É a mesma pergunta que `road.py` responde com um panorama, mas com dezenas de postes ao
longo do eixo da via em vez de dois ou três por foto. Cada poste é projetado no eixo
(referência linear): a posição ao longo da via dá o espaçamento e o lado dá a posteação.
"""

import itertools
import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from ipsurvey.domain.cadastre import CadastrePole, LinearRef, LocalFrame, RoadWay, linear_ref


@dataclass(frozen=True, slots=True)
class StreetPole:
    """Poste do cadastro referenciado no eixo de uma via."""

    pole: CadastrePole
    ref: LinearRef

    @property
    def side(self) -> str:
        """Lado em relação ao sentido de digitalização da via."""
        if abs(self.ref.offset_m) < CENTER_MAX_OFFSET_M:
            return "centro"
        return "direita" if self.ref.offset_m > 0 else "esquerda"


#: Poste a menos disto do eixo é de canteiro central (vias com o eixo no canteiro).
CENTER_MAX_OFFSET_M = 1.5


@dataclass(frozen=True, slots=True)
class StreetEstimate:
    """Atributos de uma via estimados pelo cadastro."""

    way: RoadWay
    poles: tuple[StreetPole, ...]
    spacing_m: float | None
    spacing_samples: int
    arrangement: str | None
    luminaires_per_pole: int | None
    median_offset_m: float | None


def poles_on_way(
    way: RoadWay,
    poles: Sequence[CadastrePole],
    frame: LocalFrame,
    *,
    max_offset_m: float = 20.0,
) -> list[StreetPole]:
    """Postes a até `max_offset_m` do eixo da via, com a referência linear de cada um.

    Postes de esquina ficam perto de duas vias; quem decide a qual pertencem é
    `assign_poles`, que fica com a mais próxima.
    """
    line = [frame.to_xy(lat, lon) for lat, lon in way.coords]
    length = sum(math.dist(a, b) for a, b in itertools.pairwise(line))
    out: list[StreetPole] = []
    for p in poles:
        ref = linear_ref(frame.to_xy(p.lat, p.lon), line)
        # Além das pontas, o "afastamento" seria a distância à ponta, não ao eixo.
        if abs(ref.offset_m) <= max_offset_m and 0.0 < ref.along_m < length:
            out.append(StreetPole(p, ref))
    return out


def assign_poles(
    ways: Sequence[RoadWay],
    poles: Sequence[CadastrePole],
    frame: LocalFrame,
    *,
    max_offset_m: float = 20.0,
) -> dict[str, list[StreetPole]]:
    """Cada poste vai para a via de eixo mais próximo (até `max_offset_m`)."""
    best: dict[str, tuple[float, str, StreetPole]] = {}
    for w in ways:
        for sp in poles_on_way(w, poles, frame, max_offset_m=max_offset_m):
            d = abs(sp.ref.offset_m)
            cur = best.get(sp.pole.pole_id)
            if cur is None or d < cur[0]:
                best[sp.pole.pole_id] = (d, w.way_id, sp)
    out: dict[str, list[StreetPole]] = {w.way_id: [] for w in ways}
    for _, wid, sp in best.values():
        out[wid].append(sp)
    return out


def street_estimate(
    way: RoadWay,
    poles: Sequence[StreetPole],
    *,
    min_gap_m: float = 8.0,
    max_gap_m: float = 70.0,
    front_tol: float = 0.25,
) -> StreetEstimate:
    """Espaçamento (mediana por lado), posteação e luminárias por poste de uma via."""
    by_side: dict[str, list[StreetPole]] = {}
    for sp in poles:
        by_side.setdefault(sp.side, []).append(sp)
    gaps: list[float] = []
    for line in by_side.values():
        line.sort(key=lambda s: s.ref.along_m)
        gaps += [
            b.ref.along_m - a.ref.along_m
            for a, b in itertools.pairwise(line)
            if min_gap_m <= b.ref.along_m - a.ref.along_m <= max_gap_m
        ]
    spacing = statistics.median(gaps) if gaps else None

    arrangement: str | None = None
    left, right = by_side.get("esquerda", []), by_side.get("direita", [])
    if len(poles) >= 3:
        if "centro" in by_side and len(by_side["centro"]) >= max(len(left), len(right)):
            arrangement = "Canteiro Central"
        elif not left or not right or min(len(left), len(right)) < 0.2 * len(poles):
            arrangement = "Unilateral"
        else:
            tol = front_tol * spacing if spacing else 5.0
            menor, maior = sorted((left, right), key=len)
            paired = sum(
                1 for p in menor if any(abs(p.ref.along_m - q.ref.along_m) <= tol for q in maior)
            )
            arrangement = (
                "Bilateral Frontal" if paired >= 0.6 * len(menor) else "Bilateral Alternada"
            )

    n_lum = [sp.pole.n_luminaires for sp in poles]
    return StreetEstimate(
        way=way,
        poles=tuple(poles),
        spacing_m=spacing,
        spacing_samples=len(gaps),
        arrangement=arrangement,
        luminaires_per_pole=round(statistics.median(n_lum)) if n_lum else None,
        median_offset_m=statistics.median(abs(sp.ref.offset_m) for sp in poles) if poles else None,
    )
