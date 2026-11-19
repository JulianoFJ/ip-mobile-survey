import math

import pytest

from ipsurvey.domain.geometry.equirect import angles_to_pixel, pixel_to_angles

W, H = 7680, 3840


def test_center_is_front_horizon() -> None:
    az, el = pixel_to_angles(W / 2, H / 2, W, H)
    assert az == pytest.approx(0.0)
    assert el == pytest.approx(0.0)


def test_right_is_positive_azimuth() -> None:
    az, _ = pixel_to_angles(3 * W / 4, H / 2, W, H)
    assert az == pytest.approx(math.pi / 2)


def test_top_is_zenith() -> None:
    _, el = pixel_to_angles(0, 0, W, H)
    assert el == pytest.approx(math.pi / 2)


@pytest.mark.parametrize(("u", "v"), [(-1, 0), (W, 0), (0, H)])
def test_out_of_bounds(u: float, v: float) -> None:
    with pytest.raises(ValueError, match="fora"):
        pixel_to_angles(u, v, W, H)


def test_invalid_elevation() -> None:
    with pytest.raises(ValueError, match="elevação"):
        angles_to_pixel(0.0, -math.pi / 2, W, H)
