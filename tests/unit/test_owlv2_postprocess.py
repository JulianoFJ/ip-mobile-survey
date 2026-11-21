"""Pós-processamento do OWLv2. Não carrega o modelo (nem torch)."""

from ipsurvey.adapters.detection.owlv2 import PostProcess, RawBox, iou, nms
from ipsurvey.domain.detection import BoxPx, Detection2D, StructureClass

P, L, A = StructureClass.POLE, StructureClass.LUMINAIRE, StructureClass.ARM


def _post(**kw: object) -> PostProcess:
    return PostProcess(thresholds={P: 0.3, L: 0.2, A: 0.3}, **kw)  # type: ignore[arg-type]


def test_limiar_por_classe() -> None:
    raw = [RawBox(P, 0.29, 10, 10, 20, 100), RawBox(L, 0.21, 50, 50, 70, 60)]
    out = _post()(raw, 200, 200)
    assert [d.cls for d in out] == [L]


def test_poste_largo_demais_e_descartado() -> None:
    raw = [RawBox(P, 0.9, 0, 0, 100, 120), RawBox(P, 0.9, 150, 0, 160, 100)]
    out = _post()(raw, 200, 200)
    assert len(out) == 1
    assert out[0].box.x0 == 150


def test_luminaria_alta_demais_e_o_poste_inteiro() -> None:
    raw = [RawBox(L, 0.5, 0, 0, 10, 100), RawBox(L, 0.5, 50, 50, 80, 60)]
    out = _post()(raw, 200, 200)
    assert [d.box.x0 for d in out] == [50]


def test_caixa_recortada_na_imagem_e_minuscula_descartada() -> None:
    raw = [RawBox(P, 0.9, -5, -5, 10, 120), RawBox(L, 0.9, 5, 5, 7, 7)]
    out = _post()(raw, 100, 100)
    assert len(out) == 1
    assert (out[0].box.x0, out[0].box.y0, out[0].box.y1) == (0, 0, 100)


def test_nms_mantem_a_melhor_de_cada_grupo() -> None:
    a = Detection2D(P, 0.9, BoxPx(0, 0, 10, 100))
    b = Detection2D(P, 0.5, BoxPx(1, 2, 11, 98))
    c = Detection2D(P, 0.4, BoxPx(50, 0, 60, 100))
    assert nms([b, c, a], 0.5) == [a, c]


def test_iou() -> None:
    assert iou(BoxPx(0, 0, 10, 10), BoxPx(0, 0, 10, 10)) == 1.0
    assert iou(BoxPx(0, 0, 10, 10), BoxPx(20, 20, 30, 30)) == 0.0
    assert abs(iou(BoxPx(0, 0, 10, 10), BoxPx(5, 0, 15, 10)) - 1 / 3) < 1e-9


def test_varias_descricoes_da_mesma_classe_viram_uma_deteccao() -> None:
    raw = [
        RawBox(P, 0.6, 10, 0, 20, 100, "a utility pole"),
        RawBox(P, 0.7, 11, 1, 21, 99, "a street light pole"),
    ]
    out = _post()(raw, 200, 200)
    assert len(out) == 1
    assert out[0].score == 0.7
