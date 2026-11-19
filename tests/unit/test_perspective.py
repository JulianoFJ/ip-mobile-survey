import math

import numpy as np
import pytest

from ipsurvey.domain.geometry import equirect
from ipsurvey.domain.geometry.perspective import (
    PerspectiveView,
    equirect_angles_to_pixel,
    equirect_pixel_to_angles,
    render_view,
    view_ring,
)

PW, PH = 2048, 1024


def test_vectorized_matches_scalar() -> None:
    for u, v in [(0.0, 1.0), (1024.0, 512.0), (2000.5, 900.25)]:
        az, el = equirect.pixel_to_angles(u, v, PW, PH)
        az2, el2 = equirect_pixel_to_angles(u, v, PW, PH)
        assert (az, el) == pytest.approx((float(az2), float(el2)))
        u2, v2 = equirect_angles_to_pixel(az, el, PW, PH)
        assert (float(u2), float(v2)) == pytest.approx((u, v))


@pytest.mark.parametrize(
    ("yaw", "pitch"), [(0.0, 0.0), (1.0, 0.3), (-2.5, -0.4), (math.pi - 1e-6, 0.6)]
)
def test_view_center_is_optical_axis(yaw: float, pitch: float) -> None:
    v = PerspectiveView(yaw=yaw, pitch=pitch, hfov=math.radians(90), width=640, height=480)
    az, el = v.pixel_to_angles(320.0, 240.0)
    assert float(el) == pytest.approx(pitch)
    assert math.remainder(float(az) - yaw, 2 * math.pi) == pytest.approx(0.0, abs=1e-9)


def test_horizontal_edges_at_half_fov() -> None:
    v = PerspectiveView(yaw=0.5, pitch=0.0, hfov=math.radians(90), width=800, height=600)
    az_l, el_l = v.pixel_to_angles(0.0, 300.0)
    az_r, _ = v.pixel_to_angles(800.0, 300.0)
    assert float(az_l) == pytest.approx(0.5 - math.pi / 4)
    assert float(az_r) == pytest.approx(0.5 + math.pi / 4)
    assert float(el_l) == pytest.approx(0.0)


def test_up_in_image_is_up_in_world() -> None:
    v = PerspectiveView(yaw=0.0, pitch=0.0, hfov=1.2, width=500, height=500)
    _, el_top = v.pixel_to_angles(250.0, 0.0)
    _, el_bottom = v.pixel_to_angles(250.0, 500.0)
    assert float(el_top) > 0 > float(el_bottom)


def test_behind_camera_flagged() -> None:
    v = PerspectiveView(yaw=0.0, pitch=0.0, hfov=1.2, width=100, height=100)
    _, _, front = v.angles_to_pixel(np.array([0.0, math.pi]), np.array([0.0, 0.0]))
    assert front.tolist() == [True, False]


def test_invalid_view() -> None:
    with pytest.raises(ValueError, match="hfov"):
        PerspectiveView(yaw=0, pitch=0, hfov=math.pi, width=10, height=10)
    with pytest.raises(ValueError, match="pitch"):
        PerspectiveView(yaw=0, pitch=math.pi / 2, hfov=1.0, width=10, height=10)


def _smooth_panorama() -> np.ndarray:
    """Panorama cuja cor é função contínua dos ângulos (inclusive na costura ±π)."""
    u = np.arange(PW) + 0.5
    v = np.arange(PH) + 0.5
    az, el = equirect_pixel_to_angles(*np.meshgrid(u, v), PW, PH)
    r = 128 + 100 * np.cos(az) * np.cos(el)
    g = 128 + 100 * np.sin(az) * np.cos(el)
    b = 128 + 100 * np.sin(el)
    return np.stack([r, g, b], axis=-1).round().astype(np.uint8)


@pytest.mark.parametrize("yaw", [0.0, math.pi * 0.999, -2.0])  # inclui a costura atrás
def test_render_matches_analytic_colors(yaw: float) -> None:
    pano = _smooth_panorama()
    view = PerspectiveView(yaw=yaw, pitch=0.4, hfov=math.radians(80), width=128, height=96)
    img = render_view(pano, view).astype(float)
    gx, gy = np.meshgrid(np.arange(128) + 0.5, np.arange(96) + 0.5)
    az, el = view.pixel_to_angles(gx, gy)
    expected = np.stack(
        [
            128 + 100 * np.cos(az) * np.cos(el),
            128 + 100 * np.sin(az) * np.cos(el),
            128 + 100 * np.sin(el),
        ],
        axis=-1,
    )
    assert np.abs(img - expected).max() <= 2.0


def test_render_locates_marker() -> None:
    """Um ponto marcado no panorama aparece na vista onde a projeção diz."""
    pano = np.zeros((PH, PW), dtype=np.uint8)
    az, el = 0.6, 0.5  # 34° à direita, 29° acima: altura típica de uma luminária próxima
    u, v = equirect.angles_to_pixel(az, el, PW, PH)
    pano[int(v) - 2 : int(v) + 3, int(u) - 2 : int(u) + 3] = 255
    view = PerspectiveView(yaw=0.4, pitch=0.35, hfov=math.radians(75), width=512, height=512)
    img = render_view(pano, view)
    y, x = np.unravel_index(int(np.argmax(img)), img.shape)
    ex, ey, front = view.angles_to_pixel(az, el)
    assert bool(front)
    assert abs(x + 0.5 - float(ex)) <= 3
    assert abs(y + 0.5 - float(ey)) <= 3


def test_view_ring_fits_narrow_objects_whole() -> None:
    """Todo objeto de até 20° de largura cabe inteiro em alguma vista do horizonte.

    É o que garante que um poste cortado na borda de uma vista aparece inteiro na vizinha.
    """
    views = view_ring()
    assert len(views) == 16
    horizon = [v for v in views if v.pitch == 0.0]
    half = math.radians(10)

    def inside(v: PerspectiveView, az: float) -> bool:
        x, _, front = v.angles_to_pixel(az, 0.0)
        return bool(front) and 0 <= float(x) <= v.width

    for az in np.linspace(-math.pi, math.pi, 721):
        assert any(inside(v, az - half) and inside(v, az + half) for v in horizon)


def test_view_ring_reaches_high_elevations() -> None:
    top = max(v.pitch + v.vfov / 2 for v in view_ring())
    assert math.degrees(top) >= 70
