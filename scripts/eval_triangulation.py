"""Validação da triangulação sem referência externa: foto deixada de fora.

    uv run --extra vision python scripts/eval_triangulation.py panoramax-br-v0

Para cada poste com posição de quadro único, triangula com a captura central e UMA
vizinha e prevê o rumo em que o poste deveria aparecer na OUTRA vizinha (que não entrou
no cálculo). Compara esse erro de previsão com o da posição de quadro único. Quem prevê
melhor a foto não usada tem a posição mais correta.

Não depende da BDGD, cuja coordenada (do desenho da rede) é ruidosa demais para servir
de régua no nível de poucos metros.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from eval_cross_section import ler_orientacao
from eval_cross_section import travel_az as frente_do_veiculo
from eval_zero_shot import ROOT, angular_from_cache, is_low_pole, is_tall_luminaire, load_manifest
from export_web_demo import carregar_vizinhos, raios_de

from ipsurvey.adapters.detection.owlv2 import PostProcess
from ipsurvey.domain.cadastre import LocalFrame
from ipsurvey.domain.detection import StructureClass
from ipsurvey.domain.detection.ground import ground_estimate
from ipsurvey.domain.geometry.triangulation import associate, triangulate

CAMERA_H = 1.9
PRESENTE_RAD = math.radians(10.0)  # o poste existe na foto de teste se algum raio cai a menos disto


def _dets(cp: Path, post: PostProcess) -> list:
    return [
        d
        for d in angular_from_cache(json.loads(cp.read_text("utf-8")), post)
        if not is_low_pole(d, CAMERA_H, 4.0) and not is_tall_luminaire(d)
    ]


def _ang(a: float, b: float) -> float:
    return abs(math.remainder(a - b, 2.0 * math.pi))


def main() -> None:  # noqa: PLR0915 (roteiro de avaliação, linear)
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("dataset")
    args = ap.parse_args()
    m = load_manifest(args.dataset)
    post = PostProcess()
    orient = ler_orientacao(args.dataset)
    viz, cache_viz = carregar_vizinhos(args.dataset)
    err_uni: list[float] = []
    err_tri: list[float] = []
    for it in m["items"]:
        vs = viz.get(it["id"], [])
        caches = [cache_viz / (Path(v["file"]).stem + ".json") for v in vs]
        if len(vs) < 2 or not all(c.exists() for c in caches):
            continue
        frente = frente_do_veiculo(it, orient)
        rumo = ((it["travel_bearing_deg"] or it["heading_deg"]) - math.degrees(frente)) % 360
        frame = LocalFrame(it["lat"], it["lon"])
        dets = _dets(
            ROOT / "data/eval/owlv2" / args.dataset / (Path(it["file"]).stem + ".json"), post
        )
        quadros = []
        for j, (v, cp) in enumerate(zip(vs, caches, strict=True), start=1):
            desloc = (
                v["rumo_ao_centro_deg"]
                if v["deslocamento"] < 0
                else (v["rumo_ao_centro_deg"] + 180) % 360
            )
            quadros.append(
                raios_de(
                    _dets(cp, post),
                    j,
                    frame.to_xy(v["lat"], v["lon"]),
                    desloc - math.degrees(frente),
                )
            )
        for d in dets:
            if d.cls is not StructureClass.POLE:
                continue
            est = ground_estimate(d, CAMERA_H)
            if est is None:
                continue
            b = math.radians(rumo) + d.az_center
            prior = (est.distance_m * math.sin(b), est.distance_m * math.cos(b))
            r0 = raios_de([d], 0, (0.0, 0.0), rumo)[0]
            for usar, fora in ((0, 1), (1, 0)):
                ra = associate(prior, quadros[usar])
                teste = quadros[fora]
                if ra is None or not teste:
                    continue
                t = triangulate([r0, ra], CAMERA_H)
                if t is None:
                    continue
                cx, cy = teste[0].cam_x, teste[0].cam_y

                def erro(
                    px: float, py: float, cx: float = cx, cy: float = cy, teste: list = teste
                ) -> float:
                    previsto = math.atan2(px - cx, py - cy)
                    return min(_ang(r.bearing, previsto) for r in teste)

                eu, et = erro(*prior), erro(t.x, t.y)
                if min(eu, et) < PRESENTE_RAD:
                    err_uni.append(math.degrees(eu))
                    err_tri.append(math.degrees(et))
    if not err_uni:
        print("nenhum par avaliável")
        return
    n = len(err_uni)
    q = lambda xs, f: sorted(xs)[int(f * len(xs))]  # noqa: E731
    print(f"{n} pares (poste × foto deixada de fora)")
    print(f"  quadro único: mediana {statistics.median(err_uni):.2f}°  p75 {q(err_uni, 0.75):.2f}°")
    print(f"  triangulado : mediana {statistics.median(err_tri):.2f}°  p75 {q(err_tri, 0.75):.2f}°")
    melhor = sum(t < u for t, u in zip(err_tri, err_uni, strict=True))
    print(f"  triangulado melhor em {melhor} de {n} ({100 * melhor / n:.0f}%)")


if __name__ == "__main__":
    main()
