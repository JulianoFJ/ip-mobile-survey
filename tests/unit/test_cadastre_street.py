"""Cadastro, referência linear, espaçamento por rua e casamento com o levantamento."""

import math

import pytest

from ipsurvey.domain.cadastre import (
    CadastrePoint,
    LocalFrame,
    RoadWay,
    group_poles,
    linear_ref,
    match_nearest,
)
from ipsurvey.domain.extraction.street import assign_poles, poles_on_way, street_estimate

LAT0, LON0 = -19.92, -43.94
F = LocalFrame(LAT0, LON0)
M_LAT = 1 / 111_195.0  # graus por metro (latitude)
M_LON = M_LAT / math.cos(math.radians(LAT0))


def ll(x: float, y: float) -> tuple[float, float]:
    """Metros (leste, norte) → (lat, lon)."""
    return LAT0 + y * M_LAT, LON0 + x * M_LON


def pt(i: int, x: float, y: float, **kw: object) -> CadastrePoint:
    lat, lon = ll(x, y)
    return CadastrePoint(str(i), lat, lon, **kw)  # type: ignore[arg-type]


# Via reta para o norte, de y = -200 a y = +200.
VIA = RoadWay("w1", (ll(0, -200), ll(0, 200)), "secondary", name="Av. Teste", lanes=2)


def test_frame_e_linear_ref() -> None:
    x, y = F.to_xy(*ll(10, 20))
    assert x == pytest.approx(10, abs=0.05)
    assert y == pytest.approx(20, abs=0.05)
    ref = linear_ref((7, 50), [(0, 0), (0, 100)])
    assert ref.along_m == pytest.approx(50)
    assert ref.offset_m == pytest.approx(7)  # leste é a direita de quem vai para o norte
    assert linear_ref((-7, 50), [(0, 0), (0, 100)]).offset_m == pytest.approx(-7)


def test_agrupa_luminarias_do_mesmo_poste() -> None:
    poles = group_poles([pt(1, 5, 0), pt(2, 5, 0), pt(3, 5, 30)])
    assert sorted(p.n_luminaires for p in poles) == [1, 2]


def test_unilateral_com_vao_de_35() -> None:
    poles = group_poles(pt(i, 7, -150 + 35 * i) for i in range(9))
    est = street_estimate(VIA, poles_on_way(VIA, poles, F))
    assert est.spacing_m == pytest.approx(35, abs=0.2)
    assert est.spacing_samples == 8
    assert est.arrangement == "Unilateral"
    assert est.median_offset_m == pytest.approx(7, abs=0.1)


def test_bilateral_frontal_e_alternada() -> None:
    frontal = [pt(i, 7, -100 + 40 * i) for i in range(5)] + [
        pt(10 + i, -7, -100 + 40 * i) for i in range(5)
    ]
    alternada = [pt(i, 7, -100 + 40 * i) for i in range(5)] + [
        pt(10 + i, -7, -80 + 40 * i) for i in range(5)
    ]
    ef = street_estimate(VIA, poles_on_way(VIA, group_poles(frontal), F))
    ea = street_estimate(VIA, poles_on_way(VIA, group_poles(alternada), F))
    assert ef.arrangement == "Bilateral Frontal"
    assert ea.arrangement == "Bilateral Alternada"
    assert ef.spacing_m == pytest.approx(40, abs=0.2)


def test_canteiro_central() -> None:
    est = street_estimate(
        VIA, poles_on_way(VIA, group_poles(pt(i, 0.5, -100 + 30 * i) for i in range(6)), F)
    )
    assert est.arrangement == "Canteiro Central"


def test_poste_alem_da_ponta_fica_de_fora() -> None:
    assert poles_on_way(VIA, group_poles([pt(1, 3, 230)]), F) == []


def test_poste_de_esquina_vai_para_a_via_mais_proxima() -> None:
    transversal = RoadWay("w2", (ll(-200, 0), ll(200, 0)), "residential")
    poles = group_poles([pt(1, 3, 12)])  # 3 m da w1, 12 m da w2
    out = assign_poles([VIA, transversal], poles, F)
    assert [sp.pole.pole_id for sp in out["w1"]] == ["1"]
    assert out["w2"] == []


def test_casamento_guloso_sem_repeticao() -> None:
    cad = [ll(0, 0), ll(0, 30), ll(0, 60)]
    lev = [ll(2, 1), ll(1, 29), ll(40, 40)]
    ms = match_nearest(lev, cad, F, max_m=10)
    assert {(m.survey_index, m.cadastre_index) for m in ms} == {(0, 0), (1, 1)}
    assert all(m.distance_m < 3 for m in ms)


# ---------------------------------------------------------------- fusão
from ipsurvey.domain.extraction.fusion import fuse  # noqa: E402
from ipsurvey.domain.extraction.road import RoadEstimate  # noqa: E402


def _img(**kw: object) -> RoadEstimate:
    base = dict(
        poles=(),
        luminaires=(),
        arrangement=None,
        pole_spacing_m=None,
        spacing_samples=0,
        alignment_width_m=None,
        mounting_height_m=None,
        arm_projection_m=None,
    )
    return RoadEstimate(**{**base, **kw})  # type: ignore[arg-type]


def _campo(campos: list, col: str):  # type: ignore[no-untyped-def]
    return next(c for c in campos if c.column == col)


def test_fusao_prefere_cadastro_para_vao_e_posteacao() -> None:
    poles = group_poles(pt(i, 7, -150 + 35 * i) for i in range(9))
    street = street_estimate(VIA, poles_on_way(VIA, poles, F))
    campos = fuse(
        _img(arrangement="Bilateral Frontal", pole_spacing_m=22.0, spacing_samples=1), street, VIA
    )
    af, ad, r = _campo(campos, "AF"), _campo(campos, "AD"), _campo(campos, "R")
    assert (af.source, af.value) == ("cadastro", 35.0)
    assert [c.source for c in af.candidates] == ["cadastro", "imagem"]
    assert af.divergent  # 35 × 22
    assert (ad.source, ad.value) == ("cadastro", "Unilateral")
    assert ad.divergent
    assert (r.source, r.value) == ("mapa", 2)


def test_fusao_sem_cadastro_usa_imagem_e_marca_pendente() -> None:
    campos = fuse(
        _img(arrangement="Unilateral", mounting_height_m=8.4, arm_projection_m=1.5), None, None
    )
    assert _campo(campos, "AD").source == "imagem"
    assert _campo(campos, "AL").value == 8.4
    assert _campo(campos, "AF").value is None
    assert _campo(campos, "T").value is None
    assert [c.column for c in campos][:2] == ["R", "S"]
