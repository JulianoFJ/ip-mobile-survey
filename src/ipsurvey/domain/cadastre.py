"""Cadastro de IP (ponto a ponto) e malha viária, como entram no confronto com o levantamento.

O cadastro pode vir do município ou da BDGD da ANEEL. Na BDGD, a coordenada é a do poste
da rede (PONNOT), e um poste com várias luminárias aparece como vários pontos na mesma
coordenada; `group_poles` junta esses pontos num poste.
"""

import itertools
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

EARTH_R = 6_371_008.8


@dataclass(frozen=True, slots=True)
class CadastrePoint:
    """Um ponto de IP do cadastro (uma luminária)."""

    point_id: str
    lat: float
    lon: float
    technology: str | None = None
    power_w: float | None = None
    urban: bool | None = None


@dataclass(frozen=True, slots=True)
class CadastrePole:
    """Poste do cadastro: os pontos que compartilham a coordenada."""

    pole_id: str
    lat: float
    lon: float
    points: tuple[CadastrePoint, ...]

    @property
    def n_luminaires(self) -> int:
        """Quantidade de luminárias no poste."""
        return len(self.points)


@dataclass(frozen=True, slots=True)
class RoadWay:
    """Trecho de via (eixo) do mapa, com os atributos que interessam à simulação."""

    way_id: str
    coords: tuple[tuple[float, float], ...]  # (lat, lon)
    highway: str
    name: str | None = None
    lanes: int | None = None
    oneway: bool = False
    tags: dict[str, str] = field(default_factory=dict)


def group_poles(points: Iterable[CadastrePoint], *, tol_m: float = 0.5) -> list[CadastrePole]:
    """Junta os pontos que estão na mesma coordenada (até `tol_m`) num poste."""
    cells: dict[tuple[int, int], list[CadastrePoint]] = {}
    deg = tol_m / 111_320.0
    for p in points:
        cells.setdefault((round(p.lat / deg), round(p.lon / deg)), []).append(p)
    return [
        CadastrePole(
            pole_id=pts[0].point_id,
            lat=sum(p.lat for p in pts) / len(pts),
            lon=sum(p.lon for p in pts) / len(pts),
            points=tuple(pts),
        )
        for pts in cells.values()
    ]


@dataclass(frozen=True, slots=True)
class LocalFrame:
    """Projeção plana local (equirretangular) em metros: x leste, y norte."""

    lat0: float
    lon0: float

    def to_xy(self, lat: float, lon: float) -> tuple[float, float]:
        """Graus → metros em torno da origem."""
        k = math.cos(math.radians(self.lat0))
        return (
            math.radians(lon - self.lon0) * EARTH_R * k,
            math.radians(lat - self.lat0) * EARTH_R,
        )

    def to_latlon(self, x: float, y: float) -> tuple[float, float]:
        """Metros em torno da origem → graus (inversa de `to_xy`)."""
        k = math.cos(math.radians(self.lat0))
        return (
            self.lat0 + math.degrees(y / EARTH_R),
            self.lon0 + math.degrees(x / (EARTH_R * k)),
        )


@dataclass(frozen=True, slots=True)
class LinearRef:
    """Posição de um ponto em relação a uma polilinha."""

    along_m: float
    offset_m: float  # positivo à direita do sentido de digitalização da via


def linear_ref(pt: tuple[float, float], line: Sequence[tuple[float, float]]) -> LinearRef:
    """Referência linear de `pt` na polilinha `line` (ambos em metros, mesmo referencial).

    Returns:
        Distância ao longo da linha até o pé da perpendicular e o afastamento lateral
        (com sinal: positivo à direita do sentido da linha).
    """
    if len(line) < 2:
        msg = "polilinha precisa de ao menos 2 vértices"
        raise ValueError(msg)
    best: tuple[float, float, float] | None = None  # (dist², along, offset)
    acc = 0.0
    px, py = pt
    for (ax, ay), (bx, by) in itertools.pairwise(line):
        dx, dy = bx - ax, by - ay
        seg = math.hypot(dx, dy)
        if seg == 0:
            continue
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (seg * seg)))
        qx, qy = ax + t * dx, ay + t * dy
        d2 = (px - qx) ** 2 + (py - qy) ** 2
        # vetor da via (dx, dy); à direita = produto vetorial negativo
        cross = dx * (py - ay) - dy * (px - ax)
        off = -math.copysign(math.sqrt(d2), cross) if d2 > 0 else 0.0
        if best is None or d2 < best[0]:
            best = (d2, acc + t * seg, off)
        acc += seg
    if best is None:
        msg = "polilinha degenerada"
        raise ValueError(msg)
    return LinearRef(best[1], best[2])


@dataclass(frozen=True, slots=True)
class Match:
    """Par (levantamento, cadastro) casado por proximidade."""

    survey_index: int
    cadastre_index: int
    distance_m: float


def match_nearest(
    survey: Sequence[tuple[float, float]],
    cadastre: Sequence[tuple[float, float]],
    frame: LocalFrame,
    *,
    max_m: float = 15.0,
) -> list[Match]:
    """Casa pontos do levantamento com os do cadastro, do par mais próximo ao mais distante.

    Cada ponto entra em no máximo um par (guloso por distância, sem repetição). Pares
    acima de `max_m` não casam: são poste fora do cadastro ou cadastro sem poste em campo.
    """
    s_xy = [frame.to_xy(lat, lon) for lat, lon in survey]
    c_xy = [frame.to_xy(lat, lon) for lat, lon in cadastre]
    pares = sorted(
        (math.dist(a, b), i, j)
        for i, a in enumerate(s_xy)
        for j, b in enumerate(c_xy)
        if abs(a[0] - b[0]) <= max_m and abs(a[1] - b[1]) <= max_m
    )
    usados_s: set[int] = set()
    usados_c: set[int] = set()
    out: list[Match] = []
    for d, i, j in pares:
        if d > max_m:
            break
        if i in usados_s or j in usados_c:
            continue
        usados_s.add(i)
        usados_c.add(j)
        out.append(Match(i, j, d))
    return out
