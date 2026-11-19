"""Invariantes da malha NBR 5101:2024, 5.1 (§13.1: D ≤ 3 m e N correto)."""

import math

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from ipsurvey.domain.nbr5101 import (
    calculation_grid,
    grid_size,
    sidewalk_grid,
    sidewalk_transversal_points,
)

spans = st.floats(min_value=0.5, max_value=200.0, allow_nan=False)
widths = st.floats(min_value=1.0, max_value=60.0, allow_nan=False)
lanes = st.integers(min_value=1, max_value=8)

TOL = 1e-9


@given(span=spans, n_lanes=lanes)
def test_longitudinal_spacing_at_most_3m(span: float, n_lanes: int) -> None:
    n_long, _ = grid_size(span, n_lanes)
    assert span / n_long <= 3.0 + TOL


@given(span=spans, n_lanes=lanes)
def test_n_is_minimal_and_at_least_10(span: float, n_lanes: int) -> None:
    n_long, _ = grid_size(span, n_lanes)
    assert n_long >= 10
    if n_long > 10:
        # Um ponto a menos já violaria D ≤ 3 m: N é o mínimo que cumpre a regra.
        assert span / (n_long - 1) > 3.0 - TOL


@given(span=spans, n_lanes=lanes)
def test_three_points_per_lane(span: float, n_lanes: int) -> None:
    assert grid_size(span, n_lanes)[1] == 3 * n_lanes


@given(span=spans, width=widths, n_lanes=lanes)
def test_points_strictly_inside_and_evenly_spaced(span: float, width: float, n_lanes: int) -> None:
    g = calculation_grid(span, width, n_lanes)
    assert np.all((g.x > 0) & (g.x < span))
    assert np.all((g.y > 0) & (g.y < width))
    np.testing.assert_allclose(np.diff(g.x), g.spacing_longitudinal_m, rtol=1e-9)
    np.testing.assert_allclose(np.diff(g.y), g.spacing_transversal_m, rtol=1e-9)


@given(span=spans, width=widths, n_lanes=lanes)
def test_grid_symmetric_about_span_center(span: float, width: float, n_lanes: int) -> None:
    # Centro das células ⇒ malha simétrica; bilateral e alternado dão a mesma média.
    g = calculation_grid(span, width, n_lanes)
    np.testing.assert_allclose(g.x + g.x[::-1], span, rtol=1e-9)
    np.testing.assert_allclose(g.y + g.y[::-1], width, rtol=1e-9)


@given(span=spans, width=widths, n_lanes=lanes)
def test_lane_center_rows_at_lane_centers(span: float, width: float, n_lanes: int) -> None:
    g = calculation_grid(span, width, n_lanes)
    lane_w = width / n_lanes
    expected = [(k + 0.5) * lane_w for k in range(n_lanes)]
    assert all(
        math.isclose(a, b, rel_tol=1e-9)
        for a, b in zip(g.y[g.lane_center_rows()], expected, strict=True)
    )


sidewalk_widths = st.floats(min_value=0.5, max_value=20.0, allow_nan=False)


@given(width=sidewalk_widths)
def test_sidewalk_transversal_rule(width: float) -> None:
    c = sidewalk_transversal_points(width)
    if width <= 4.5:
        assert c == 3
    else:
        assert width / c <= 1.5 + TOL  # d ≤ 1,5 m
        assert width / (c - 1) > 1.5 - TOL  # c é o mínimo


@given(span=spans, width=sidewalk_widths)
def test_sidewalk_points_inside_and_symmetric(span: float, width: float) -> None:
    g = sidewalk_grid(span, width)
    assert g.shape[0] == grid_size(span)[0]  # longitudinal igual à pista (5.1.2.2)
    assert np.all((g.y > 0) & (g.y < width))
    np.testing.assert_allclose(g.y + g.y[::-1], width, rtol=1e-9)
