"""Triangulação em cena sintética: três câmeras ao longo de uma rua, postes conhecidos."""

import math
import random

import pytest

from ipsurvey.domain.geometry.triangulation import Ray, associate, intersect, triangulate

H = 1.9
CAMS = [(0.0, -6.0), (0.0, 0.0), (0.0, 6.0)]  # carro andando para o norte, fotos a cada 6 m


def raio(frame: int, px: float, py: float, h: float = 9.0, ruido_rad: float = 0.0) -> Ray:
    cx, cy = CAMS[frame]
    d = math.hypot(px - cx, py - cy)
    return Ray(
        frame=frame,
        cam_x=cx,
        cam_y=cy,
        bearing=math.atan2(px - cx, py - cy) + ruido_rad,
        el_min=-math.atan(H / d),
        el_max=math.atan((h - H) / d),
    )


def test_interseccao_exata() -> None:
    res = intersect([raio(0, 7, 20), raio(2, 7, 20)])
    assert res is not None
    x, y, rms = res
    assert (x, y) == pytest.approx((7, 20), abs=1e-6)
    assert rms == pytest.approx(0, abs=1e-6)


def test_triangula_posicao_e_altura_com_ruido() -> None:
    rnd = random.Random(1)
    rays = [raio(f, 8, 15, h=10.0, ruido_rad=rnd.gauss(0, math.radians(0.5))) for f in range(3)]
    t = triangulate(rays, H)
    assert t is not None
    assert math.hypot(t.x - 8, t.y - 15) < 1.0
    assert t.height_m == pytest.approx(10.0, abs=0.5)
    assert t.n_rays == 3


def test_recusa_raios_quase_paralelos() -> None:
    # Poste muito à frente, no eixo da rua: os raios das três câmeras quase coincidem.
    assert triangulate([raio(0, 0.5, 120), raio(2, 0.5, 120)], H) is None


def test_recusa_raios_de_postes_diferentes() -> None:
    assert triangulate([raio(0, 7, 20), raio(2, -7, 20)], H) is None


def test_recusa_ponto_atras_da_camera() -> None:
    r0 = raio(0, 7, 20)
    oposto = Ray(2, 0.0, 6.0, raio(2, 7, 20).bearing + math.pi, 0.0, 0.1)
    assert intersect([r0, oposto]) is None


def test_associa_o_raio_que_aponta_para_o_poste() -> None:
    candidatos = [raio(2, -7, 25), raio(2, 7, 20), raio(2, 12, 40)]
    escolhido = associate((7.8, 21.0), candidatos)  # posição aproximada, com erro
    assert escolhido is candidatos[1]
    assert associate((30.0, -30.0), candidatos) is None
