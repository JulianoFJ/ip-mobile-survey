"""Malha de pontos de cálculo e medição de iluminância por vão (ABNT NBR 5101:2024, 5.1).

Regras (conferidas no texto da NBR 5101:2024 em 19/11/2026):

* **Longitudinal, pista e calçada (5.1.1.1 e 5.1.2.2):** D = S/N ≤ 3 m. Se S ≤ 30 m,
  N = 10; se S > 30 m, N é o menor inteiro com D ≤ 3 m. Ou seja, N = máx(10, ⌈S/3⌉).
  O primeiro ponto fica a D/2 do poste.
* **Transversal, pista (5.1.1.2):** sempre 3 pontos por faixa de trânsito, d = L/3. O ponto
  central fica no eixo da faixa e os extremos a d/2 do meio-fio ou da linha de divisa.
* **Transversal, calçada (5.1.2.1):** largura ≤ 4,5 m → 3 pontos; largura > 4,5 m → menor
  inteiro c com d = largura/c ≤ 1,5 m. Extremos a d/2 das bordas.

Nos dois eixos, os pontos ficam no **centro das células**. É a mesma malha de
`malha_en13201` na Plataforma_IP, validada contra o DIALux (Cajamar, 2026).

Convenção de eixos (local ao vão, em metros):
    * x: longitudinal, de 0 (primeiro poste) a S (poste seguinte);
    * y: transversal, de 0 (borda de referência) à largura da área.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from ipsurvey.domain.errors import DataValidationError

MAX_LONGITUDINAL_SPACING_M = 3.0
MIN_LONGITUDINAL_POINTS = 10
POINTS_PER_LANE = 3
SIDEWALK_MIN_POINTS = 3
SIDEWALK_NARROW_MAX_WIDTH_M = 4.5
SIDEWALK_MAX_TRANSVERSAL_SPACING_M = 1.5

# Absorve ruído de ponto flutuante: S = 30.000000000000004 não deve virar N = 11.
_EPS = 1e-9


class Area(StrEnum):
    """Tipo de área calculada."""

    ROADWAY = "roadway"
    SIDEWALK = "sidewalk"


def longitudinal_points(span_m: float) -> int:
    """Número N de pontos ao longo do vão (5.1.1.1).

    Args:
        span_m: Vão S entre postes consecutivos, em metros (> 0).

    Returns:
        N = 10 se S ≤ 30 m; senão o menor inteiro com S/N ≤ 3 m.

    Raises:
        DataValidationError: Se `span_m` não for finito e positivo.
    """
    _require_positive("vão", span_m)
    return max(MIN_LONGITUDINAL_POINTS, math.ceil(span_m / MAX_LONGITUDINAL_SPACING_M - _EPS))


def sidewalk_transversal_points(width_m: float) -> int:
    """Número c de pontos na largura da calçada (5.1.2.1).

    Args:
        width_m: Largura da calçada, em metros (> 0).

    Returns:
        3 se largura ≤ 4,5 m; senão o menor inteiro com largura/c ≤ 1,5 m.

    Raises:
        DataValidationError: Se `width_m` não for finito e positivo.
    """
    _require_positive("largura", width_m)
    if width_m <= SIDEWALK_NARROW_MAX_WIDTH_M + _EPS:
        return SIDEWALK_MIN_POINTS
    return math.ceil(width_m / SIDEWALK_MAX_TRANSVERSAL_SPACING_M - _EPS)


def grid_size(span_m: float, lanes: int = 1) -> tuple[int, int]:
    """Número de pontos da malha da pista de um vão.

    Args:
        span_m: Vão S entre postes consecutivos, em metros (> 0).
        lanes: Número de faixas de trânsito (≥ 1).

    Returns:
        (n_longitudinal, n_transversal).

    Raises:
        DataValidationError: Se `span_m` ≤ 0 ou `lanes` < 1.
    """
    _require_lanes(lanes)
    return longitudinal_points(span_m), POINTS_PER_LANE * lanes


@dataclass(frozen=True)
class CalculationGrid:
    """Malha de cálculo de um vão, nas coordenadas locais do vão (metros).

    Attributes:
        area: Pista ou calçada.
        span_m: Vão S.
        width_m: Largura da área calculada.
        lanes: Número de faixas de trânsito (pista) ou 0 (calçada).
        x: Posições longitudinais, em (0, S), crescentes.
        y: Posições transversais, em (0, largura), crescentes.
    """

    area: Area
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
        """Espaçamento d entre pontos na largura (m)."""
        return self.width_m / len(self.y)

    def lane_center_rows(self) -> list[int]:
        """Índices em `y` da linha central de cada faixa (o ponto do meio de cada trinca).

        É sobre essas linhas que se calcula a uniformidade longitudinal (Ul).

        Raises:
            ValueError: Se a malha for de calçada (não há faixas).
        """
        if self.area is not Area.ROADWAY:
            msg = "linhas centrais de faixa só existem na malha da pista"
            raise ValueError(msg)
        return [lane * POINTS_PER_LANE + 1 for lane in range(self.lanes)]

    def meshgrid(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Matrizes (X, Y) com forma (n_longitudinal, n_transversal)."""
        xx, yy = np.meshgrid(self.x, self.y, indexing="ij")
        return xx, yy


def calculation_grid(span_m: float, width_m: float, lanes: int = 1) -> CalculationGrid:
    """Malha da pista (área de trânsito de veículos) de um vão (5.1.1).

    Args:
        span_m: Vão S entre postes, em metros (> 0).
        width_m: Largura total da pista, em metros (> 0). As faixas têm largura igual.
        lanes: Número de faixas de trânsito (≥ 1).

    Returns:
        CalculationGrid com os pontos no centro das células.

    Raises:
        DataValidationError: Se algum argumento for inválido.
    """
    _require_positive("largura", width_m)
    n_long, n_trans = grid_size(span_m, lanes)
    return CalculationGrid(
        area=Area.ROADWAY,
        span_m=span_m,
        width_m=width_m,
        lanes=lanes,
        x=_cell_centers(span_m, n_long),
        y=_cell_centers(width_m, n_trans),
    )


def sidewalk_grid(span_m: float, width_m: float) -> CalculationGrid:
    """Malha da calçada de um vão (5.1.2).

    Args:
        span_m: Vão S entre postes, em metros (> 0).
        width_m: Largura da calçada, do meio-fio à divisa do lote, em metros (> 0).

    Returns:
        CalculationGrid com os pontos no centro das células.

    Raises:
        DataValidationError: Se algum argumento for inválido.
    """
    return CalculationGrid(
        area=Area.SIDEWALK,
        span_m=span_m,
        width_m=width_m,
        lanes=0,
        x=_cell_centers(span_m, longitudinal_points(span_m)),
        y=_cell_centers(width_m, sidewalk_transversal_points(width_m)),
    )


def _cell_centers(length_m: float, n: int) -> NDArray[np.float64]:
    return (np.arange(n, dtype=np.float64) + 0.5) * (length_m / n)


def _require_positive(name: str, value: float) -> None:
    if not (math.isfinite(value) and value > 0):
        msg = f"{name} deve ser finito(a) e > 0 m, recebido {value}"
        raise DataValidationError(msg)


def _require_lanes(lanes: int) -> None:
    if lanes < 1:
        msg = f"número de faixas deve ser ≥ 1, recebido {lanes}"
        raise DataValidationError(msg)
