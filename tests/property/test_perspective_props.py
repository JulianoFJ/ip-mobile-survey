"""Invariantes das vistas planas: ida e volta pixel ↔ ângulo."""

import math

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from ipsurvey.domain.geometry.perspective import PerspectiveView

views = st.builds(
    PerspectiveView,
    yaw=st.floats(min_value=-math.pi, max_value=math.pi),
    pitch=st.floats(min_value=-1.2, max_value=1.2),
    hfov=st.floats(min_value=0.3, max_value=2.5),
    width=st.integers(min_value=16, max_value=2048),
    height=st.integers(min_value=16, max_value=2048),
)


@given(view=views, fx=st.floats(0, 1), fy=st.floats(0, 1))
def test_pixel_roundtrip(view: PerspectiveView, fx: float, fy: float) -> None:
    x, y = fx * view.width, fy * view.height
    az, el = view.pixel_to_angles(x, y)
    x2, y2, front = view.angles_to_pixel(az, el)
    assert bool(front)
    assert math.isclose(float(x2), x, abs_tol=1e-6 * view.width + 1e-6)
    assert math.isclose(float(y2), y, abs_tol=1e-6 * view.height + 1e-6)


@given(view=views)
def test_vfov_consistent_with_edges(view: PerspectiveView) -> None:
    # Na coluna central, a diferença de elevação entre topo e base é o vfov (pitch 0).
    flat = PerspectiveView(
        yaw=view.yaw, pitch=0.0, hfov=view.hfov, width=view.width, height=view.height
    )
    _, el_top = flat.pixel_to_angles(view.width / 2, 0.0)
    _, el_bot = flat.pixel_to_angles(view.width / 2, float(view.height))
    assert math.isclose(float(el_top - el_bot), flat.vfov, rel_tol=1e-9)


@given(yaw=st.floats(-math.pi, math.pi), dyaw=st.floats(-0.5, 0.5), el=st.floats(-0.5, 0.5))
def test_points_inside_fov_project_inside_view(yaw: float, dyaw: float, el: float) -> None:
    view = PerspectiveView(yaw=yaw, pitch=0.0, hfov=1.6, width=1000, height=1000)
    x, y, front = view.angles_to_pixel(yaw + dyaw, el)
    assert bool(front)
    assert 0 <= float(x) <= 1000
    assert 0 <= float(y) <= 1000
    assert np.isfinite([float(x), float(y)]).all()
