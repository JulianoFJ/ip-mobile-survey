import math

import numpy as np
import pytest
from numpy.typing import NDArray

from ipsurvey.application.use_cases.detect_structures import DetectStructures
from ipsurvey.domain.detection import (
    AngularDetection,
    BoxPx,
    Detection2D,
    StructureClass,
    merge_detections,
    to_angular,
)
from ipsurvey.domain.geometry.perspective import (
    PerspectiveView,
    equirect_pixel_to_angles,
    view_ring,
)

POLE = StructureClass.POLE
LUM = StructureClass.LUMINAIRE
PW, PH = 2048, 1024
rad = math.radians


# ---------------------------------------------------------------- contratos
def test_box_and_score_validation() -> None:
    with pytest.raises(ValueError, match="degenerada"):
        BoxPx(10, 10, 10, 20)
    with pytest.raises(ValueError, match="score"):
        Detection2D(POLE, 1.5, BoxPx(0, 0, 1, 1))


def test_to_angular_centered_box() -> None:
    view = PerspectiveView(yaw=0.7, pitch=0.0, hfov=rad(90), width=1000, height=1000)
    a = to_angular(Detection2D(POLE, 0.8, BoxPx(490, 300, 510, 700)), view, view_index=3)
    assert a.az_center == pytest.approx(0.7, abs=1e-9)
    assert a.el_max == pytest.approx(-a.el_min, abs=1e-9)
    assert a.el_max == pytest.approx(math.atan(200 / 500), abs=1e-3)
    assert not a.truncated
    assert a.views == (3,)


def test_to_angular_flags_cut_edges() -> None:
    view = PerspectiveView(yaw=0.0, pitch=0.0, hfov=rad(90), width=100, height=100)
    a = to_angular(Detection2D(POLE, 0.8, BoxPx(40, 0, 60, 100)), view)
    assert a.cut_top
    assert a.cut_bottom
    assert not a.cut_side
    b = to_angular(Detection2D(POLE, 0.8, BoxPx(97, 40, 100, 60)), view)
    assert b.cut_side
    assert not b.cut_top


def _det(az: float, el0: float, el1: float, **kw: object) -> AngularDetection:
    base: dict[str, object] = {
        "cls": POLE,
        "score": 0.9,
        "az_center": az,
        "az_half_width": rad(1),
        "el_min": el0,
        "el_max": el1,
    }
    base.update(kw)
    return AngularDetection(**base)  # type: ignore[arg-type]


def test_az_overlap_across_seam() -> None:
    a = _det(math.pi - rad(0.5), 0, 1)
    b = _det(-math.pi + rad(0.5), 0, 1)
    assert a.az_overlap(b) == pytest.approx(0.5, abs=1e-9)


def test_merge_joins_pole_pieces_from_two_rows() -> None:
    bottom = _det(0.3, rad(-20), rad(37), cut_top=True, views=(1,))
    top = _det(0.3 + rad(0.2), rad(-2), rad(45), cut_bottom=True, score=0.7, views=(9,))
    [m] = merge_detections([top, bottom])
    assert m.el_min == pytest.approx(rad(-20))
    assert m.el_max == pytest.approx(rad(45))
    assert not m.truncated
    assert m.views == (1, 9)
    assert m.score == 0.9


def test_merge_prefers_whole_sides_for_azimuth() -> None:
    cut = _det(0.30, 0, 1, cut_side=True, score=0.99)
    whole = _det(0.31, 0, 1, score=0.6)
    [m] = merge_detections([cut, whole])
    assert m.az_center == pytest.approx(0.31)
    assert not m.cut_side


def test_merge_keeps_separate_objects_and_classes() -> None:
    dets = [
        _det(0.3, 0, 1),
        _det(0.9, 0, 1),  # outro poste
        _det(0.3, 0.2, 0.4, cls=LUM),  # luminária no mesmo azimute: outra classe
        _det(0.3, rad(60), rad(70)),  # mesmo azimute, mas longe em elevação
    ]
    assert len(merge_detections(dets)) == 4


# ---------------------------------------------------------------- ponta a ponta sintético
def _panorama_with_pole(az0: float, el0: float, el1: float) -> NDArray[np.uint8]:
    u = np.arange(PW) + 0.5
    v = np.arange(PH) + 0.5
    az, el = equirect_pixel_to_angles(*np.meshgrid(u, v), PW, PH)
    daz = np.abs(np.remainder(az - az0 + math.pi, 2 * math.pi) - math.pi)
    pole = (daz <= rad(1.0)) & (el >= el0) & (el <= el1)
    img = np.full((PH, PW, 3), 40, dtype=np.uint8)
    img[pole] = 255
    return img


class BrightBlobDetector:
    """Detector falso: cada faixa contígua de colunas claras vira uma caixa de poste."""

    def detect(self, image: NDArray[np.uint8]) -> list[Detection2D]:
        mask = image.mean(axis=2) > 150
        cols = np.flatnonzero(mask.any(axis=0))
        if cols.size == 0:
            return []
        runs = np.split(cols, np.flatnonzero(np.diff(cols) > 1) + 1)
        out = []
        for run in runs:
            rows = np.flatnonzero(mask[:, run].any(axis=1))
            box = BoxPx(run[0], rows[0], run[-1] + 1, rows[-1] + 1)
            out.append(Detection2D(POLE, 0.9, box))
        return out


@pytest.mark.parametrize(
    ("az0", "el0", "el1"),
    [
        (0.3, rad(-20), rad(45)),  # poste alto e próximo: nenhuma vista vê inteiro
        (math.pi - rad(0.3), rad(-20), rad(45)),  # na costura ±180°
        (-1.9, rad(-8), rad(15)),  # poste distante, cabe numa vista
    ],
)
def test_detect_structures_recovers_pole(az0: float, el0: float, el1: float) -> None:
    detect = DetectStructures(BrightBlobDetector(), view_ring(size=256))
    [pole] = detect(_panorama_with_pole(az0, el0, el1))
    assert pole.cls is POLE
    assert math.remainder(pole.az_center - az0, 2 * math.pi) == pytest.approx(0, abs=rad(0.5))
    assert pole.el_min == pytest.approx(el0, abs=rad(1))
    assert pole.el_max == pytest.approx(el1, abs=rad(1))
    assert not pole.cut_top
    assert not pole.cut_bottom


def test_detect_structures_empty_panorama() -> None:
    pano = np.full((PH, PW, 3), 40, dtype=np.uint8)
    assert DetectStructures(BrightBlobDetector(), view_ring(size=128))(pano) == []
