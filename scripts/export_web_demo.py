"""Exporta os resultados da avaliação zero-shot para a interface web (dados de demonstração).

    uv run --extra vision python scripts/export_web_demo.py panoramax-br-v0

Lê o manifesto do golden dataset e o cache do `eval_zero_shot.py run`, aplica o mesmo
pós-processamento da galeria e grava em web/public/demo/ (fora do git):

* `campanhas.json`: lista de inspeções;
* `campanha-<dataset>.json`: capturas com detecções em ângulos, altura e distância
  estimadas e posição de cada poste no mapa;
* `img/<arquivo>.jpg`: panoramas reduzidos para o visualizador.

O formato é o contrato que a API vai servir depois (ver web/src/dados/tipos.ts).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from eval_zero_shot import (
    ROOT,
    angular_from_cache,
    is_low_pole,
    is_tall_luminaire,
    load_manifest,
)
from PIL import Image

from ipsurvey.adapters.detection.owlv2 import DEFAULT_PROMPTS, DEFAULT_THRESHOLDS, PostProcess
from ipsurvey.domain.detection import StructureClass
from ipsurvey.domain.detection.ground import ground_estimate

EARTH_R = 6_371_008.8


def destination(lat: float, lon: float, bearing_deg: float, dist_m: float) -> tuple[float, float]:
    """Ponto a `dist_m` metros de (lat, lon) no rumo `bearing_deg` (esfera)."""
    phi1, lam1, th = map(math.radians, (lat, lon, bearing_deg))
    delta = dist_m / EARTH_R
    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(th)
    )
    lam2 = lam1 + math.atan2(
        math.sin(th) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), (math.degrees(lam2) + 540) % 360 - 180


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    ap.add_argument("--camera-height", type=float, default=1.9)
    ap.add_argument("--min-pole-height", type=float, default=4.0)
    ap.add_argument("--width", type=int, default=2048, help="largura das imagens exportadas")
    args = ap.parse_args()

    m = load_manifest(args.dataset)
    src = ROOT / m["local_dir"]
    cache_dir = ROOT / "data/eval/owlv2" / args.dataset
    out = ROOT / "web/public/demo"
    (out / "img").mkdir(parents=True, exist_ok=True)
    post = PostProcess()

    capturas = []
    for it in m["items"]:
        cpath = cache_dir / (Path(it["file"]).stem + ".json")
        if not cpath.exists():
            continue
        cache = json.loads(cpath.read_text("utf-8"))
        dets = [
            d
            for d in angular_from_cache(cache, post)
            if not is_low_pole(d, args.camera_height, args.min_pole_height)
            and not is_tall_luminaire(d)
        ]
        img_name = Path(it["file"]).stem + ".jpg"
        dest_img = out / "img" / img_name
        if not dest_img.exists():
            im = Image.open(src / it["file"]).convert("RGB")
            im.resize((args.width, args.width // 2), Image.Resampling.LANCZOS).save(
                dest_img, quality=82, optimize=True
            )
        deteccoes = []
        for k, d in enumerate(dets):
            est = ground_estimate(d, args.camera_height) if d.cls is StructureClass.POLE else None
            lat = lon = None
            if est is not None:
                bearing = it["heading_deg"] + math.degrees(d.az_center)
                lat, lon = destination(it["lat"], it["lon"], bearing, est.distance_m)
            deteccoes.append(
                {
                    "id": f"{it['id'][:8]}-{k:02d}",
                    "classe": d.cls.value,
                    "score": round(d.score, 3),
                    "az": round(d.az_center, 5),
                    "azMeia": round(d.az_half_width, 5),
                    "elMin": round(d.el_min, 5),
                    "elMax": round(d.el_max, 5),
                    "cortadoBase": d.cut_bottom,
                    "cortadoTopo": d.cut_top,
                    "alturaM": round(est.height_m, 2) if est else None,
                    "alturaMinima": est.height_is_lower_bound if est else False,
                    "distanciaM": round(est.distance_m, 2) if est else None,
                    "lat": round(lat, 7) if lat is not None else None,
                    "lon": round(lon, 7) if lon is not None else None,
                }
            )
        capturas.append(
            {
                "id": it["id"],
                "arquivo": it["file"],
                "imagem": f"demo/img/{img_name}",
                "cidade": it["city"],
                "lat": it["lat"],
                "lon": it["lon"],
                "rumo": it["heading_deg"],
                "data": it["captured"],
                "camera": it["camera"],
                "autor": it["author"],
                "licenca": it["license"],
                "origem": f"https://api.panoramax.xyz/#focus=pic&pic={it['id']}",
                "deteccoes": deteccoes,
            }
        )

    campanha = {
        "id": args.dataset,
        "nome": "Avaliação do detector — vias urbanas brasileiras",
        "municipio": f"{len({c['cidade'] for c in capturas})} cidades (golden {args.dataset})",
        "status": "em_revisao",
        "criadaEm": m["retrieved"],
        "fonte": m["source"],
        "licenca": m["attribution"],
        "modelo": "OWLv2 base (zero-shot)",
        "parametros": {
            "alturaCameraM": args.camera_height,
            "alturaMinimaPosteM": args.min_pole_height,
            "limiares": {c.value: v for c, v in DEFAULT_THRESHOLDS.items()},
            "descricoes": {c.value: list(v) for c, v in DEFAULT_PROMPTS.items()},
        },
        "capturas": capturas,
    }
    (out / f"campanha-{args.dataset}.json").write_text(
        json.dumps(campanha, ensure_ascii=False), "utf-8"
    )
    resumo = {k: campanha[k] for k in ("id", "nome", "municipio", "status", "criadaEm", "modelo")}
    resumo["capturas"] = len(capturas)
    resumo["postes"] = sum(d["classe"] == "poste" for c in capturas for d in c["deteccoes"])
    (out / "campanhas.json").write_text(json.dumps([resumo], ensure_ascii=False), "utf-8")
    print(f"{out}: {len(capturas)} capturas, {resumo['postes']} postes")


if __name__ == "__main__":
    main()
