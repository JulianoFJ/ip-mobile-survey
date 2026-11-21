"""Corte transversal em cenas sintéticas: grade pintada à mão e panorama renderizado."""

import math

import numpy as np
import pytest

from ipsurvey.adapters.segmentation.oneformer import tabela_de_classes
from ipsurvey.domain.extraction.cross_section import (
    GroundClass,
    GroundGrid,
    cross_section,
    front_from_axis,
    ground_grid,
    ground_views,
    road_axis,
)

R, S, V, C, OUT = (
    GroundClass.ROAD,
    GroundClass.SIDEWALK,
    GroundClass.VEGETATION,
    GroundClass.VEHICLE,
    GroundClass.OTHER,
)
CELL = 0.1
XS = np.arange(-20 + CELL / 2, 20, CELL)
YS = np.arange(-10 + CELL / 2, 15, CELL)


def pintar(faixas: list[tuple[float, float, GroundClass]]) -> GroundGrid:
    """Grade com faixas longitudinais [x0, x1) de cada classe; o resto é OTHER."""
    lab = np.zeros((len(YS), len(XS)), np.uint8)
    for x0, x1, c in faixas:
        lab[:, (x0 <= XS) & (x1 > XS)] = c
    return GroundGrid(lab, XS, YS)


def test_rua_simples_com_passeios() -> None:
    # carro a 2 m da borda esquerda; pista de 7 m; passeios de 2,5 e 3 m.
    g = pintar([(-4.5, -2, S), (-2, 5, R), (5, 8, S)])
    cs = cross_section(g)
    assert cs.road_width_m == pytest.approx(7.0, abs=0.15)
    assert cs.curb_left_m == pytest.approx(2.0, abs=0.1)
    assert cs.sidewalk_left_m == pytest.approx(2.5, abs=0.15)
    assert cs.sidewalk_right_m == pytest.approx(3.0, abs=0.15)
    assert cs.median_m is None


def test_carro_estacionado_conta_como_pista_e_ruido_some() -> None:
    g = pintar([(-3, 4, R), (4, 6, C), (6, 8, S)])
    g.labels[::7, (XS > 1.0) & (XS < 1.2)] = OUT  # manchas finas de ruído
    cs = cross_section(g)
    assert cs.road_width_m == pytest.approx(9.0, abs=0.15)


def test_canteiro_central_e_segunda_pista() -> None:
    g = pintar([(-3, -1.5, S), (-1.5, 7, R), (7, 10, V), (10, 17, R), (17, 19, S)])
    cs = cross_section(g)
    assert cs.road_width_m == pytest.approx(8.5, abs=0.15)
    assert cs.median_m == pytest.approx(3.0, abs=0.15)
    assert cs.median_side == "direita"
    assert cs.road2_width_m == pytest.approx(7.0, abs=0.15)


def test_pista_que_sai_da_grade_nao_tem_largura() -> None:
    g = pintar([(-20, 20, R)])
    cs = cross_section(g)
    assert cs.road_width_m is None


def test_projecao_no_chao_com_vistas_reais() -> None:
    """Rótulo constante por vista: a grade recebe o rótulo da vista que vê cada célula."""
    views = ground_views(size=256)
    # Vista apontando para a frente (yaw 0) diz pista; as demais, passeio.
    labs = [np.full((256, 256), R if abs(v.yaw) < 1e-9 else S, np.uint8) for v in views]
    g = ground_grid(labs, views, 1.9, cell_m=0.25)
    i = int(np.searchsorted(g.ys, 8.0))
    j0 = int(np.searchsorted(g.xs, 0.0))
    assert g.labels[i, j0] == R  # 8 m à frente: vista frontal
    j = int(np.searchsorted(g.xs, 8.0))
    i0 = int(np.searchsorted(g.ys, 0.5))
    assert g.labels[i0, j] == S  # 8 m à direita: vista lateral
    # com o deslocamento girado 90°, a frente passa a ser vista pela vista lateral
    g2 = ground_grid(labs, views, 1.9, travel_az=math.pi / 2, cell_m=0.25)
    assert g2.labels[i, j0] == S


def test_tabela_ade20k_para_classes_do_chao() -> None:
    lut = tabela_de_classes(
        {0: "wall", 6: "road, route", 11: "sidewalk, pavement", 9: "grass", 20: "car, auto"}
    )
    assert [lut[6], lut[11], lut[9], lut[20], lut[0]] == [R, S, V, C, OUT]


@pytest.mark.parametrize("ang_deg", [0, 30, 90, 135])
def test_eixo_da_pista(ang_deg: float) -> None:
    gx, gy = np.meshgrid(XS, YS)
    a = math.radians(ang_deg)  # azimute do eixo: direção (sin a, cos a)
    dist_lateral = np.abs(gx * math.cos(a) - gy * math.sin(a))
    lab = np.where(dist_lateral <= 4.0, R, S).astype(np.uint8)
    ax = road_axis(GroundGrid(lab, XS, YS))
    assert ax is not None
    assert abs(math.remainder(ax.az - a, math.pi)) < math.radians(2)
    assert ax.anisotropy > 3


def test_frente_resolve_o_sentido_pelo_esperado() -> None:
    assert front_from_axis(math.radians(85), math.radians(90)) == pytest.approx(math.radians(85))
    assert front_from_axis(math.radians(85), math.radians(-90)) == pytest.approx(math.radians(-95))


def test_canteiro_com_varias_faixas_e_mureta() -> None:
    gramado = pintar(
        [(-16, -10, R), (-10, -9.5, S), (-9.5, -6, V), (-6, -5.5, S), (-5.5, 4, R), (4, 6, S)]
    )
    cs = cross_section(gramado)
    assert cs.median_m == pytest.approx(4.5, abs=0.15)
    assert cs.median_side == "esquerda"
    assert cs.sidewalk_left_m is None
    assert cs.sidewalk_right_m == pytest.approx(2.0, abs=0.15)
    mureta = pintar([(-12, -3.6, R), (-3.6, -3, OUT), (-3, 4, R), (4, 9, OUT)])
    cm = cross_section(mureta)
    assert cm.median_m == pytest.approx(0.6, abs=0.15)
    assert cm.road_width_m == pytest.approx(7.0, abs=0.15)


def test_predio_largo_nao_e_canteiro() -> None:
    cs = cross_section(pintar([(-12, -9, R), (-9, -6, OUT), (-6, 4, R), (4, 6, S)]))
    assert cs.median_m is None


def test_patio_de_estacionamento_nao_conta_como_pista() -> None:
    patio = pintar([(-3, 4, R), (4, 12, C), (12, 14, S)])  # 8 m de carros, sem pista depois
    assert cross_section(patio).road_width_m == pytest.approx(7.0, abs=0.15)
    no_transito = pintar([(-3, 2, R), (2, 6, C), (6, 8, R), (8, 10, S)])  # carros entre pistas
    assert cross_section(no_transito).road_width_m == pytest.approx(11.0, abs=0.15)


def test_pedaco_curto_de_pista_nao_cria_canteiro() -> None:
    g = pintar([(-3, 2, R), (2, 2.7, OUT), (2.7, 4, R), (4, 6, S)])
    assert cross_section(g).median_m is None
