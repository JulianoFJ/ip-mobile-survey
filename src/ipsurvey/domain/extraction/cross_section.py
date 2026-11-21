"""Larguras da via a partir da segmentação do chão num panorama (corte transversal).

Cadeia:

1. `ground_views`: vistas planas inclinadas para baixo, onde o chão aparece com boa
   resolução (a 10 m, ~0,1 m por pixel numa vista de 1024 px e 100°);
2. um segmentador (adaptador) rotula cada pixel em `GroundClass`;
3. `ground_grid`: cada célula do chão, no referencial do deslocamento (x à direita, y à
   frente), é projetada nas vistas e recebe o rótulo da vista que a vê mais de frente;
4. `cross_section`: em cada fatia transversal perto da câmera, parte do carro (que está na
   pista) e anda para os dois lados, juntando as faixas de mesma classe. A mediana das
   fatias dá a largura da pista, dos passeios e, quando há pista dos dois lados de uma faixa
   de verde ou passeio, do canteiro central.

Hipóteses: chão plano, câmera a `camera_height_m`, carro dentro da pista. Veículo conta
como pista quando há pista depois dele ou quando é uma fileira estacionada (faixa de
estacionamento, que é parte da via); pátio de estacionamento não conta.
"""

import math
import statistics
from dataclasses import dataclass
from enum import IntEnum

import numpy as np
from numpy.typing import NDArray

from ipsurvey.domain.geometry.perspective import PerspectiveView


class GroundClass(IntEnum):
    """Classes do chão que interessam ao corte transversal."""

    OTHER = 0
    ROAD = 1
    SIDEWALK = 2
    VEGETATION = 3
    VEHICLE = 4


def ground_views(
    *, n_yaw: int = 8, pitch_deg: float = -30.0, hfov_deg: float = 100.0, size: int = 1024
) -> list[PerspectiveView]:
    """Vistas inclinadas para baixo, em volta do panorama (8 × 45°, com sobreposição)."""
    step = 2.0 * math.pi / n_yaw
    return [
        PerspectiveView(
            yaw=math.remainder(k * step, 2.0 * math.pi),
            pitch=math.radians(pitch_deg),
            hfov=math.radians(hfov_deg),
            width=size,
            height=size,
        )
        for k in range(n_yaw)
    ]


@dataclass(frozen=True)
class GroundGrid:
    """Rótulos do chão numa grade regular (linhas = y, colunas = x)."""

    labels: NDArray[np.uint8]
    xs: NDArray[np.float64]
    ys: NDArray[np.float64]

    @property
    def cell_m(self) -> float:
        """Lado da célula (m)."""
        return float(self.xs[1] - self.xs[0])


def ground_grid(  # noqa: PLR0913 (geometria da grade, só keyword)
    labels: list[NDArray[np.uint8]],
    views: list[PerspectiveView],
    camera_height_m: float,
    travel_az: float = 0.0,
    *,
    x_range: tuple[float, float] = (-20.0, 20.0),
    y_range: tuple[float, float] = (-10.0, 15.0),
    cell_m: float = 0.1,
    vehicle_box: tuple[float, float] = (1.2, 2.6),
) -> GroundGrid:
    """Projeta os rótulos das vistas no chão.

    Cada célula fica com o rótulo da vista em que cai mais perto do centro (menos
    distorção). Células que nenhuma vista vê ficam `OTHER`. A área do próprio veículo
    (meia largura e meio comprimento em `vehicle_box`) vira pista: o capô e o teto
    aparecem na imagem, mas embaixo deles há pista.
    """
    xs = np.arange(x_range[0] + cell_m / 2, x_range[1], cell_m)
    ys = np.arange(y_range[0] + cell_m / 2, y_range[1], cell_m)
    gx, gy = np.meshgrid(xs, ys)
    r = np.hypot(gx, gy)
    az = np.arctan2(gx, gy) + travel_az
    el = -np.arctan2(camera_height_m, np.maximum(r, 1e-6))
    out = np.zeros(gx.shape, np.uint8)
    best = np.full(gx.shape, np.inf)
    for lab, v in zip(labels, views, strict=True):
        px, py, front = v.angles_to_pixel(az, el)
        ok = front & (px >= 0) & (px < v.width) & (py >= 0) & (py < v.height)
        dist = np.hypot(px - v.width / 2, py - v.height / 2)
        take = ok & (dist < best)
        ix = np.clip(px.astype(int), 0, v.width - 1)
        iy = np.clip(py.astype(int), 0, v.height - 1)
        out[take] = lab[iy[take], ix[take]]
        best[take] = dist[take]
    hw, hl = vehicle_box
    out[(np.abs(gx) <= hw) & (np.abs(gy) <= hl)] = GroundClass.ROAD
    return GroundGrid(out, xs, ys)


@dataclass(frozen=True, slots=True)
class Band:
    """Faixa contínua de uma classe, a partir do carro (distâncias laterais positivas)."""

    cls: GroundClass
    start_m: float
    end_m: float
    open_end: bool  # chegou ao limite da grade: a largura é um mínimo

    @property
    def width_m(self) -> float:
        """Largura da faixa."""
        return self.end_m - self.start_m


#: Uma fileira de carros estacionados ocupa até isto. Faixa de veículos mais larga, sem
#: pista depois, é estacionamento fora da via (pátio, recuo), não faixa de rolamento.
MAX_PARKING_M = 2.6


def _runs(vals: NDArray[np.uint8]) -> list[list[int]]:
    """[classe, início, fim) de cada trecho contínuo."""
    runs: list[list[int]] = []
    for i, v in enumerate(vals):
        if runs and runs[-1][0] == v:
            runs[-1][2] = i + 1
        else:
            runs.append([int(v), i, i + 1])
    return runs


def _bands(row: NDArray[np.uint8], cell: float, min_run_m: float) -> list[Band]:
    """Faixas de um lado (row[0] encostado no carro), com ruído curto absorvido.

    Veículo vira pista quando há pista depois dele (carro no meio do trânsito) ou quando é
    uma fileira estacionada encostada na pista (até `MAX_PARKING_M`). Mais largo que isso e
    sem pista depois, vira OTHER: a borda da pista fica antes dele.
    """
    runs = _runs(row)
    resolved = row.copy()
    for k, (c, a, b) in enumerate(runs):
        if c != GroundClass.VEHICLE:
            continue
        antes = runs[k - 1][0] if k > 0 else GroundClass.ROAD
        depois = runs[k + 1][0] if k + 1 < len(runs) else None
        if depois == GroundClass.ROAD or (
            antes == GroundClass.ROAD and (b - a) * cell <= MAX_PARKING_M
        ):
            resolved[a:b] = GroundClass.ROAD
        else:
            resolved[a:b] = GroundClass.OTHER
    min_cells = max(1, round(min_run_m / cell))
    merged: list[list[int]] = []
    for run in _runs(resolved):
        if run[2] - run[1] < min_cells and merged:
            merged[-1][2] = run[2]  # ruído: incorpora à faixa anterior
        elif merged and merged[-1][0] == run[0]:
            merged[-1][2] = run[2]
        else:
            merged.append(run)
    n = len(row)
    return [Band(GroundClass(c), a * cell, b * cell, b == n) for c, a, b in merged]


@dataclass(frozen=True, slots=True)
class SideProfile:
    """O que há de um lado do carro numa fatia."""

    curb_m: float | None  # borda da pista a partir do eixo do carro
    curb_open: bool
    sidewalk_m: float | None
    median_m: float | None
    road2_m: float | None


def _side(bands: list[Band]) -> SideProfile:
    """Lê as faixas de um lado: pista do carro, depois canteiro + pista, ou passeio.

    Canteiro é tudo o que fica entre a pista do carro e outra pista, até `MAX_MEDIAN_M`:
    pode ter várias faixas (passeio, grama, passeio) e mureta ou defensa (OTHER estreito,
    até `MAX_BARRIER_M`). Sem outra pista ao alcance, a primeira faixa de passeio é o passeio.
    """
    if not bands or bands[0].cls != GroundClass.ROAD:
        return SideProfile(None, False, None, None, None)
    curb = bands[0]
    if curb.open_end:
        return SideProfile(None, True, None, None, None)
    rest = bands[1:]
    acumulado = 0.0
    for b in rest:
        if b.cls == GroundClass.ROAD:
            # Pedaço curto de "pista" depois de uma faixa estreita é erro de segmentação
            # (pessoa, bueiro, sombra), não a pista do outro lado de um canteiro.
            if 0 < acumulado <= MAX_MEDIAN_M and (b.open_end or b.width_m >= MIN_ROAD2_M):
                return SideProfile(
                    curb.end_m, False, None, acumulado, None if b.open_end else b.width_m
                )
            break
        if b.open_end or (b.cls == GroundClass.OTHER and b.width_m > MAX_BARRIER_M):
            break
        acumulado += b.width_m
        if acumulado > MAX_MEDIAN_M:
            break
    sidewalk = None
    if rest and rest[0].cls == GroundClass.SIDEWALK and not rest[0].open_end:
        sidewalk = rest[0].width_m
    return SideProfile(curb.end_m, False, sidewalk, None, None)


#: Largura mínima da pista do outro lado para a faixa do meio contar como canteiro.
MIN_ROAD2_M = 2.5
#: Mureta, defensa ou meio-fio largo entre pistas (OTHER estreito) ainda é canteiro.
MAX_BARRIER_M = 2.0
#: Faixa entre duas pistas mais larga que isto não é canteiro (é quadra, praça).
MAX_MEDIAN_M = 15.0


@dataclass(frozen=True, slots=True)
class CrossSection:
    """Larguras medianas das fatias válidas. `None` quando não há fatias suficientes."""

    road_width_m: float | None  # pista onde está o carro, meio-fio a meio-fio
    curb_left_m: float | None  # distância lateral do eixo do carro ao meio-fio esquerdo
    curb_right_m: float | None
    sidewalk_left_m: float | None
    sidewalk_right_m: float | None
    median_m: float | None
    median_side: str | None
    road2_width_m: float | None
    rows_used: int
    rows_total: int


def _med(xs: list[float], n_min: int) -> float | None:
    return statistics.median(xs) if len(xs) >= n_min else None


def cross_section(
    grid: GroundGrid,
    *,
    y_window: tuple[float, float] = (-6.0, 10.0),
    min_run_m: float = 0.4,
    min_fraction: float = 0.3,
) -> CrossSection:
    """Corte transversal mediano nas fatias de `y_window` (perto da câmera)."""
    cell = grid.cell_m
    i0 = int(np.searchsorted(grid.xs, 0.0))
    rows = [i for i, y in enumerate(grid.ys) if y_window[0] <= y <= y_window[1]]
    acc: dict[str, list[float]] = {k: [] for k in ("w", "l", "r", "sl", "sr", "m", "r2")}
    lado_canteiro: list[str] = []
    for i in rows:
        row = grid.labels[i]
        left = _side(_bands(row[:i0][::-1], cell, min_run_m))
        right = _side(_bands(row[i0:], cell, min_run_m))
        if left.curb_m is not None:
            acc["l"].append(left.curb_m)
        if right.curb_m is not None:
            acc["r"].append(right.curb_m)
        if left.curb_m is not None and right.curb_m is not None:
            acc["w"].append(left.curb_m + right.curb_m)
        if left.sidewalk_m is not None:
            acc["sl"].append(left.sidewalk_m)
        if right.sidewalk_m is not None:
            acc["sr"].append(right.sidewalk_m)
        for nome, s in (("esquerda", left), ("direita", right)):
            if s.median_m is not None:
                acc["m"].append(s.median_m)
                lado_canteiro.append(nome)
                if s.road2_m is not None:
                    acc["r2"].append(s.road2_m)
    n_min = max(3, int(min_fraction * len(rows)))
    median = _med(acc["m"], n_min)
    return CrossSection(
        road_width_m=_med(acc["w"], n_min),
        curb_left_m=_med(acc["l"], n_min),
        curb_right_m=_med(acc["r"], n_min),
        sidewalk_left_m=_med(acc["sl"], n_min),
        sidewalk_right_m=_med(acc["sr"], n_min),
        median_m=median,
        median_side=statistics.mode(lado_canteiro) if median is not None else None,
        road2_width_m=_med(acc["r2"], n_min) if median is not None else None,
        rows_used=len(acc["w"]),
        rows_total=len(rows),
    )


@dataclass(frozen=True, slots=True)
class RoadAxis:
    """Direção da pista em volta da câmera, no referencial do panorama."""

    az: float  # azimute do panorama (rad) ao longo da pista, em [0, π): sem sentido
    anisotropy: float  # razão entre os eixos principais; perto de 1 = sem direção clara
    cells: int


def road_axis(grid: GroundGrid, *, r_min: float = 3.0, r_max: float = 10.0) -> RoadAxis | None:
    """Eixo principal das células de pista num anel em volta da câmera.

    A grade deve estar no referencial do panorama (`travel_az=0`). Usa um anel (não a
    grade inteira, que é retangular) para não puxar o eixo para o lado mais comprido. Em
    cruzamento a anisotropia cai: quem usa decide o mínimo aceitável.
    """
    gx, gy = np.meshgrid(grid.xs, grid.ys)
    r = np.hypot(gx, gy)
    sel = (grid.labels == GroundClass.ROAD) & (r >= r_min) & (r <= r_max)
    n = int(sel.sum())
    if n < 50:
        return None
    x, y = gx[sel], gy[sel]
    cov = np.cov(np.stack([x, y]))
    vals, vecs = np.linalg.eigh(cov)
    vx, vy = vecs[:, 1]  # maior autovalor
    az = math.atan2(vx, vy) % math.pi
    return RoadAxis(az, float(vals[1] / max(vals[0], 1e-9)), n)


def front_from_axis(axis_az: float, prior_az: float) -> float:
    """Frente do veículo no panorama: o sentido do eixo mais próximo do esperado."""
    cands = (axis_az, axis_az + math.pi)
    best = min(cands, key=lambda a: abs(math.remainder(a - prior_az, 2.0 * math.pi)))
    return math.remainder(best, 2.0 * math.pi)
