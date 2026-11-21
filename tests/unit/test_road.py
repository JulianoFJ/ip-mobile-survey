"""Cena sintética: via reta, câmera no eixo a 1,9 m, postes e luminárias conhecidos."""

import math

import pytest

from ipsurvey.domain.detection import AngularDetection, StructureClass
from ipsurvey.domain.extraction.road import Side, estimate_road, plan_poles, pole_spacing

H_CAM = 1.9


def _pole(x: float, y: float, h: float = 9.0) -> AngularDetection:
    d = math.hypot(x, y)
    return AngularDetection(
        cls=StructureClass.POLE,
        score=0.8,
        az_center=math.atan2(x, y),
        az_half_width=0.2 / d,
        el_min=-math.atan(H_CAM / d),
        el_max=math.atan((h - H_CAM) / d),
    )


def _lum(x: float, y: float, h: float) -> AngularDetection:
    r = math.hypot(x, y)
    el = math.atan((h - H_CAM) / r)
    return AngularDetection(
        cls=StructureClass.LUMINAIRE,
        score=0.5,
        az_center=math.atan2(x, y),
        az_half_width=0.3 / r,
        el_min=el - 0.01,
        el_max=el + 0.01,
    )


def test_projecao_no_chao_e_lados() -> None:
    poles = plan_poles([_pole(6, 20), _pole(-6, 35), _pole(0.5, 15)], H_CAM)
    assert [p.side for p in poles] == [Side.RIGHT, Side.LEFT, Side.CENTER]
    assert poles[0].x_m == pytest.approx(6)
    assert poles[0].y_m == pytest.approx(20)
    assert poles[0].height_m == pytest.approx(9)


def test_vao_unilateral() -> None:
    # O de 75 m tem o pé a 1,45° abaixo do horizonte: longe demais, fica de fora.
    dets = [_pole(7, y) for y in (-30, 5, 40, 75)]
    est = estimate_road(dets, H_CAM)
    assert len(est.poles) == 3
    assert est.pole_spacing_m == pytest.approx(35)
    assert est.spacing_samples == 2
    assert est.arrangement == "Unilateral"
    assert est.alignment_width_m is None


def test_vao_ignora_buraco_e_duplicata() -> None:
    poles = plan_poles([_pole(7, y) for y in (0, 3, 35, 140)], H_CAM)
    spacing, n = pole_spacing(poles)
    assert spacing == pytest.approx(32)  # 0→3 duplicata, 35→140 buraco
    assert n == 1


def test_bilateral_frontal_e_alternada() -> None:
    frontal = [_pole(7, y) for y in (10, 45)] + [_pole(-8, y) for y in (11, 46)]
    alternada = [_pole(7, y) for y in (10, 45)] + [_pole(-8, y) for y in (27, 62)]
    ef = estimate_road(frontal, H_CAM)
    ea = estimate_road(alternada, H_CAM)
    assert ef.arrangement == "Bilateral Frontal"
    assert ea.arrangement == "Bilateral Alternada"
    assert ef.alignment_width_m == pytest.approx(15)


def test_canteiro_central() -> None:
    est = estimate_road([_pole(0.8, y) for y in (15, 50)], H_CAM)
    assert est.arrangement == "Canteiro Central"


def test_altura_de_instalacao_e_braco() -> None:
    # Poste à direita a 7 m do eixo; braço de 2 m para dentro da via; luminária a 8,5 m.
    dets = [_pole(7, 20), _lum(5, 20, 8.5)]
    est = estimate_road(dets, H_CAM)
    assert len(est.luminaires) == 1
    assert est.mounting_height_m == pytest.approx(8.5)
    assert est.arm_projection_m == pytest.approx(2.0)


def test_luminaria_de_poste_ao_lado_fica_de_fora() -> None:
    # Poste quase a 90°: a hipótese y_l = y_p não determina x_l.
    est = estimate_road([_pole(7, 1), _lum(5, 1, 8.5)], H_CAM)
    assert est.luminaires == ()
    assert est.mounting_height_m is None


def test_sem_postes() -> None:
    est = estimate_road([], H_CAM)
    assert est.arrangement is None
    assert est.pole_spacing_m is None


def test_sentido_de_deslocamento_girado() -> None:
    """Câmera com o centro da imagem 100° à direita da frente do veículo."""
    rot = math.radians(100)
    base = [_pole(7, y) for y in (10, 45)] + [_pole(-8, y) for y in (27, 62)] + [_lum(5, 10, 8.5)]
    girado = [
        AngularDetection(
            **{
                **{f: getattr(d, f) for f in d.__slots__},
                "az_center": math.remainder(d.az_center + rot, 2 * math.pi),
            }
        )
        for d in base
    ]
    a = estimate_road(base, H_CAM)
    b = estimate_road(girado, H_CAM, travel_az=rot)
    assert b.arrangement == a.arrangement == "Bilateral Alternada"
    assert b.pole_spacing_m == pytest.approx(a.pole_spacing_m)
    assert b.alignment_width_m == pytest.approx(15)
    assert b.mounting_height_m == pytest.approx(8.5)


def test_luz_baixa_perto_do_poste_nao_e_luminaria() -> None:
    """Semáforo a 4 m ao lado de um poste de 9 m: não vira luminária daquele poste."""
    est = estimate_road([_pole(7, 20), _lum(6, 20, 4.0)], H_CAM)
    assert est.luminaires == ()


def test_alinhamentos_ignoram_postes_distantes() -> None:
    dets = [_pole(7, 10), _pole(-8, 12), _pole(-40, 60)]
    assert estimate_road(dets, H_CAM).alignment_width_m == pytest.approx(15)
