import math

import pytest

from ipsurvey.domain.detection import AngularDetection, StructureClass
from ipsurvey.domain.detection.ground import ground_estimate


def _pole(el_min_deg: float, el_max_deg: float, **kw: bool) -> AngularDetection:
    return AngularDetection(
        cls=StructureClass.POLE,
        score=0.9,
        az_center=0.0,
        az_half_width=0.01,
        el_min=math.radians(el_min_deg),
        el_max=math.radians(el_max_deg),
        **kw,
    )


def test_poste_de_9m_a_15m() -> None:
    h_cam, d, h = 1.9, 15.0, 9.0
    det = _pole(-math.degrees(math.atan(h_cam / d)), math.degrees(math.atan((h - h_cam) / d)))
    est = ground_estimate(det, h_cam)
    assert est is not None
    assert est.distance_m == pytest.approx(d)
    assert est.height_m == pytest.approx(h)
    assert not est.height_is_lower_bound


def test_placa_baixa_fica_abaixo_da_camera_mais_pouco() -> None:
    est = ground_estimate(_pole(-14.4, 1.8), 1.9)
    assert est is not None
    assert est.height_m < 3.0


def test_pe_cortado_ou_no_horizonte_nao_estima() -> None:
    assert ground_estimate(_pole(-10, 30, cut_bottom=True), 1.9) is None
    assert ground_estimate(_pole(-1, 10), 1.9) is None


def test_topo_cortado_vira_limite_inferior() -> None:
    est = ground_estimate(_pole(-8, 40, cut_top=True), 1.9)
    assert est is not None
    assert est.height_is_lower_bound


def test_altura_da_camera_invalida() -> None:
    with pytest.raises(ValueError, match="positiva"):
        ground_estimate(_pole(-8, 20), 0.0)
