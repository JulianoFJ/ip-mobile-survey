"""Triangulação de postes vistos em quadros consecutivos.

Num quadro só, a distância de um poste vem do ângulo do pé abaixo do horizonte (chão plano)
e erra quando o pé está escondido ou o chão não é plano. Com dois ou três quadros, cada
detecção é uma semirreta no mapa (posição da câmera + rumo da detecção) e o poste fica na
interseção. A altura sai do ângulo do topo e da distância triangulada, sem depender do pé.

Referencial local no chão: x leste, y norte (metros). Rumo em radianos, a partir do norte,
sentido horário: direção (sin θ, cos θ).

As posições relativas entre quadros vizinhos vêm do GPS da câmera: o erro absoluto é de
metros, mas entre fotos tiradas a segundos de distância ele é quase o mesmo e se cancela
em boa parte.
"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class Ray:
    """Detecção de um poste num quadro, como semirreta no chão."""

    frame: int
    cam_x: float
    cam_y: float
    bearing: float  # rad, do norte, horário
    el_min: float  # elevação do pé (rad)
    el_max: float  # elevação do topo (rad)
    cut_top: bool = False

    def direction(self) -> tuple[float, float]:
        """Vetor unitário do rumo."""
        return math.sin(self.bearing), math.cos(self.bearing)


@dataclass(frozen=True, slots=True)
class Triangulated:
    """Poste triangulado."""

    x: float
    y: float
    height_m: float | None
    height_is_lower_bound: bool
    n_rays: int
    rms_m: float  # distância média quadrática do ponto aos raios
    spread_rad: float  # maior ângulo entre os raios usados (geometria da interseção)


def intersect(rays: Sequence[Ray]) -> tuple[float, float, float] | None:
    """Ponto mais próximo de todas as retas (mínimos quadrados) e o RMS das distâncias.

    Cada reta contribui com a restrição n·p = n·c, sendo n a normal ao rumo. Devolve None
    se as retas são paralelas (sistema mal condicionado) ou se o ponto cai atrás de alguma
    câmera (a detecção é uma semirreta, não uma reta).
    """
    if len(rays) < 2:
        return None
    a = np.zeros((2, 2))
    b = np.zeros(2)
    for r in rays:
        n = np.array([math.cos(r.bearing), -math.sin(r.bearing)])
        a += np.outer(n, n)
        b += n * (n @ np.array([r.cam_x, r.cam_y]))
    if np.linalg.cond(a) > 1e6:
        return None
    p = np.linalg.solve(a, b)
    d2 = []
    for r in rays:
        dx, dy = p[0] - r.cam_x, p[1] - r.cam_y
        ux, uy = r.direction()
        if dx * ux + dy * uy <= 0:  # atrás da câmera
            return None
        d2.append((dx * uy - dy * ux) ** 2)
    return float(p[0]), float(p[1]), math.sqrt(sum(d2) / len(d2))


def spread(rays: Sequence[Ray]) -> float:
    """Maior ângulo entre dois raios do conjunto (rad, de 0 a π)."""
    best = 0.0
    for i, r in enumerate(rays):
        for s in rays[i + 1 :]:
            best = max(best, abs(math.remainder(r.bearing - s.bearing, 2.0 * math.pi)))
    return best


def triangulate(
    rays: Sequence[Ray],
    camera_height_m: float,
    *,
    min_spread: float = math.radians(4.0),
    max_rms_m: float = 1.5,
) -> Triangulated | None:
    """Triangula um poste a partir de raios de quadros diferentes.

    Recusa geometria fraca: raios quase paralelos (menos de `min_spread` entre eles) dão
    interseção instável ao longo da linha de visada; e RMS acima de `max_rms_m` indica que
    os raios não são do mesmo poste.
    """
    if len({r.frame for r in rays}) < 2:
        return None
    sp = spread(rays)
    if sp < min_spread:
        return None
    res = intersect(rays)
    if res is None:
        return None
    x, y, rms = res
    if rms > max_rms_m:
        return None
    alturas = [
        camera_height_m + math.hypot(x - r.cam_x, y - r.cam_y) * math.tan(r.el_max) for r in rays
    ]
    lower = all(r.cut_top for r in rays)
    return Triangulated(x, y, statistics.median(alturas), lower, len(rays), rms, sp)


def associate(
    prior_xy: tuple[float, float],
    candidates: Sequence[Ray],
    *,
    min_tol: float = math.radians(3.0),
    lateral_tol_m: float = 4.0,
) -> Ray | None:
    """Escolhe, num quadro vizinho, o raio que aponta para a posição aproximada do poste.

    A tolerância angular é o maior entre `min_tol` e o ângulo que `lateral_tol_m` subtende
    à distância prevista: poste perto aceita desvio angular maior. Entre os que passam,
    fica o de menor desvio.
    """
    best: tuple[float, Ray] | None = None
    for r in candidates:
        dx, dy = prior_xy[0] - r.cam_x, prior_xy[1] - r.cam_y
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            continue
        previsto = math.atan2(dx, dy)
        desvio = abs(math.remainder(r.bearing - previsto, 2.0 * math.pi))
        tol = max(min_tol, math.atan2(lateral_tol_m, dist))
        if desvio <= tol and (best is None or desvio < best[0]):
            best = (desvio, r)
    return best[1] if best else None
