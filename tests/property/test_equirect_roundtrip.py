"""Invariante: pixel → ângulos → pixel é a identidade (§13.1)."""

import math

from hypothesis import given
from hypothesis import strategies as st

from ipsurvey.domain.geometry.equirect import angles_to_pixel, pixel_to_angles

W, H = 7680, 3840


@given(
    u=st.floats(min_value=0, max_value=W, exclude_max=True),
    v=st.floats(min_value=0, max_value=H, exclude_max=True, exclude_min=True),
)
def test_pixel_roundtrip(u: float, v: float) -> None:
    az, el = pixel_to_angles(u, v, W, H)
    u2, v2 = angles_to_pixel(az, el, W, H)
    assert math.isclose(u2 % W, u, abs_tol=1e-6) or math.isclose(abs(u2 - u), W, abs_tol=1e-6)
    assert math.isclose(v2, v, abs_tol=1e-6)


@given(az=st.floats(min_value=-50, max_value=50), k=st.integers(min_value=-5, max_value=5))
def test_azimuth_periodic(az: float, k: int) -> None:
    u1, _ = angles_to_pixel(az, 0.0, W, H)
    u2, _ = angles_to_pixel(az + 2 * math.pi * k, 0.0, W, H)
    diff = abs(u1 - u2)
    assert diff < 1e-6 or abs(diff - W) < 1e-6
