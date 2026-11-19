import math

import numpy as np
import pytest

from ipsurvey.domain.errors import DataValidationError
from ipsurvey.domain.nbr5101 import (
    Area,
    calculation_grid,
    grid_size,
    longitudinal_points,
    sidewalk_grid,
    sidewalk_transversal_points,
)


@pytest.mark.parametrize(
    ("span", "lanes", "expected"),
    [
        # Casos conferidos contra o DIALux na Plataforma_IP (Cajamar, 2026):
        # 3, 6 e 12 linhas para 1, 2 e 4 faixas; 10 a 14 colunas para vãos de 19 a 40 m.
        (19.0, 1, (10, 3)),
        (30.0, 2, (10, 6)),
        (31.0, 2, (11, 6)),
        (35.0, 4, (12, 12)),
        (40.0, 1, (14, 3)),
    ],
)
def test_grid_size_reference_cases(span: float, lanes: int, expected: tuple[int, int]) -> None:
    assert grid_size(span, lanes) == expected


def test_float_noise_does_not_add_column() -> None:
    assert grid_size(0.1 * 300, 1) == (10, 3)  # 0.1*300 = 30.000000000000004


def test_points_at_cell_centers() -> None:
    g = calculation_grid(30.0, 7.0, lanes=2)
    np.testing.assert_allclose(g.x, np.arange(10) * 3.0 + 1.5)
    np.testing.assert_allclose(g.y[:3], [7 / 12, 3 * 7 / 12, 5 * 7 / 12])


def test_lane_center_rows_hit_lane_centers() -> None:
    g = calculation_grid(30.0, 7.0, lanes=2)
    centers = g.y[g.lane_center_rows()]
    np.testing.assert_allclose(centers, [7 / 4, 3 * 7 / 4])


def test_meshgrid_shape() -> None:
    g = calculation_grid(35.0, 10.5, lanes=3)
    xx, yy = g.meshgrid()
    assert xx.shape == yy.shape == g.shape == (12, 9)


@pytest.mark.parametrize(
    ("span", "width", "lanes"),
    [(0, 7, 1), (-5, 7, 1), (math.inf, 7, 1), (30, 0, 1), (30, math.nan, 1), (30, 7, 0)],
)
def test_invalid_inputs(span: float, width: float, lanes: int) -> None:
    with pytest.raises(DataValidationError):
        calculation_grid(span, width, lanes)


# ---------------------------------------------------------------- NBR 5101:2024, 5.1.1.1
@pytest.mark.parametrize(
    ("span", "n"), [(5.0, 10), (30.0, 10), (30.01, 11), (33.0, 11), (45.0, 15)]
)
def test_longitudinal_rule_30m_threshold(span: float, n: int) -> None:
    assert longitudinal_points(span) == n


# ---------------------------------------------------------------- NBR 5101:2024, 5.1.2.1
@pytest.mark.parametrize(
    ("width", "c"), [(1.2, 3), (3.0, 3), (4.5, 3), (4.51, 4), (6.0, 4), (6.01, 5), (9.0, 6)]
)
def test_sidewalk_transversal_rule(width: float, c: int) -> None:
    assert sidewalk_transversal_points(width) == c


def test_sidewalk_grid() -> None:
    g = sidewalk_grid(35.0, 6.0)
    assert g.area is Area.SIDEWALK
    assert g.shape == (12, 4)
    np.testing.assert_allclose(g.y, [0.75, 2.25, 3.75, 5.25])  # d = 1,5 m; extremos a d/2


def test_sidewalk_has_no_lane_rows() -> None:
    with pytest.raises(ValueError, match="pista"):
        sidewalk_grid(30.0, 3.0).lane_center_rows()


@pytest.mark.parametrize(("span", "width"), [(0, 3), (30, 0), (30, -1), (math.nan, 3)])
def test_sidewalk_invalid_inputs(span: float, width: float) -> None:
    with pytest.raises(DataValidationError):
        sidewalk_grid(span, width)
