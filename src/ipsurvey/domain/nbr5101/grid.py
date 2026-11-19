"""Malha de pontos de cálculo para um vão de via (NBR 5101 / EN 13201-3).

Regra (a mesma de `malha_en13201` na Plataforma_IP, validada contra o DIALux em 33 grades
de 10 relatórios, Cajamar 2026):

* **Longitudinal:** N = máx(10, ⌈S / 3⌉) pontos no vão S, logo espaçamento D = S/N ≤ 3 m.
* **Transversal:** 3 pontos por faixa de rolamento (o passeio, quando calculado, conta como
  uma faixa).
* Os pontos ficam no **centro das células**. Incluir as duas bordas contaria duas vezes a
  mesma fase do arranjo periódico (o início e o fim do vão são o mesmo ponto).

Convenção de eixos (local ao vão, em metros):
    * x: longitudinal, de 0 (primeiro poste) a S (poste seguinte);
    * y: transversal, de 0 (meio-fio de referência) a W (meio-fio oposto).
"""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ipsurvey.domain.errors import DataValidationError

MAX_LONGITUDINAL_SPACING_M = 3.0
MIN_LONGITUDINAL_POINTS = 10
POINTS_PER_LANE = 3

# Absorve ruído de ponto flutuante: S = 30.000000000000004 não deve virar N = 11.
_EPS = 1e-9


def grid_size(span_m: float, lanes: int = 1) -> tuple[int, int]:
    """Número de pontos da malha de um vão.

    Args:
        span_m: Vão S entre postes consecutivos, em metros (> 0).
        lanes: Número de faixas de rolamento (≥ 1).

    Returns:
        (n_longitudinal, n_transversal).

    Raises:
        DataValidationError: Se `span_m` ≤ 0 ou `lanes` < 1.
    """
    _validate(span_m=span_m, lanes=lanes)
    n_long = max(MIN_LONGITUDINAL_POINTS, math.ceil(span_m / MAX_LONGITUDINAL_SPACING_M - _EPS))
    return n_long, POINTS_PER_LANE * lanes


@dataclass(frozen=True)
class CalculationGrid:
    """Malha de cálculo de um vão, nas coordenadas locais do vão (metros).

    Attributes:
        span_m: Vão S.
        width_m: Largura W da área calculada (pista).
        lanes: Número de faixas.
        x: Posições longitudinais, em (0, S), crescentes.
        y: Posições transversais, em (0, W), crescentes.
    """

    span_m: float
    width_m: float
    lanes: int
    x: NDArray[np.float64]
    y: NDArray[np.float64]

    @property
    def shape(self) -> tuple[int, int]:
        """(n_longitudinal, n_transversal)."""
        return len(self.x), len(self.y)

    @property
    def spacing_longitudinal_m(self) -> float:
        """Espaçamento D entre pontos ao longo do vão (m)."""
        return self.span_m / len(self.x)

    @property
    def spacing_transversal_m(self) -> float:
        """Espaçamento entre pontos na largura (m)."""
        return self.width_m / len(self.y)

    def lane_center_rows(self) -> list[int]:
        """Índices em `y` da linha central de cada faixa (o ponto do meio de cada trinca).

        É sobre essas linhas que se calcula a uniformidade longitudinal (Ul).
        """
        return [lane * POINTS_PER_LANE + 1 for lane in range(self.lanes)]

    def meshgrid(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Matrizes (X, Y) com forma (n_longitudinal, n_transversal)."""
        xx, yy = np.meshgrid(self.x, self.y, indexing="ij")
        return xx, yy


def calculation_grid(span_m: float, width_m: float, lanes: int = 1) -> CalculationGrid:
    """Gera a malha de cálculo de um vão.

    Args:
        span_m: Vão S entre postes, em metros (> 0).
        width_m: Largura W da pista, em metros (> 0).
        lanes: Número de faixas de rolamento (≥ 1).

    Returns:
        CalculationGrid com os pontos no centro das células.

    Raises:
        DataValidationError: Se algum argumento for inválido.
    """
    _validate(span_m=span_m, lanes=lanes, width_m=width_m)
    n_long, n_trans = grid_size(span_m, lanes)
    x = (np.arange(n_long, dtype=np.float64) + 0.5) * (span_m / n_long)
    y = (np.arange(n_trans, dtype=np.float64) + 0.5) * (width_m / n_trans)
    return CalculationGrid(span_m=span_m, width_m=width_m, lanes=lanes, x=x, y=y)


def _validate(*, span_m: float, lanes: int, width_m: float | None = None) -> None:
    if not (math.isfinite(span_m) and span_m > 0):
        msg = f"vão deve ser finito e > 0 m, recebido {span_m}"
        raise DataValidationError(msg)
    if width_m is not None and not (math.isfinite(width_m) and width_m > 0):
        msg = f"largura deve ser finita e > 0 m, recebida {width_m}"
        raise DataValidationError(msg)
    if lanes < 1:
        msg = f"número de faixas deve ser ≥ 1, recebido {lanes}"
        raise DataValidationError(msg)
