"""Exporta os resultados para a interface web (dados de demonstração).

    uv run --extra vision python scripts/export_web_demo.py panoramax-br-v0 \\
        --bdgd-dir ../Plataforma_IP/app/cadastro_bdgd/data/cadastros

Lê o manifesto do golden dataset e o cache do `eval_zero_shot.py run`, aplica o mesmo
pós-processamento da galeria e funde três fontes por captura:

* imagem 360°: postes, luminárias, altura, braço (`domain/extraction/road.py`);
* cadastro BDGD (parquets publicados pelo Ignis): vão e posteação por rua, lâmpadas por
  poste, tecnologia e potência (`domain/extraction/street.py`);
* mapa (OSM via Overpass, com cache em data/osm/): eixo, nome, classe e faixas da via.

Grava em web/public/demo/ (fora do git): `campanhas.json`, `campanha-<dataset>.json` e
`img/`. O formato é o contrato que a API vai servir depois (web/src/dados/tipos.ts).
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
from pathlib import Path

from eval_zero_shot import ROOT, angular_from_cache, is_low_pole, is_tall_luminaire, load_manifest
from PIL import Image

from ipsurvey.adapters.cadastre.bdgd import BdgdParquetCadastre
from ipsurvey.adapters.detection.owlv2 import DEFAULT_PROMPTS, DEFAULT_THRESHOLDS, PostProcess
from ipsurvey.adapters.maps.overpass import OverpassRoads
from ipsurvey.domain.cadastre import (
    CadastrePole,
    LocalFrame,
    RoadWay,
    group_poles,
    linear_ref,
)
from ipsurvey.domain.detection import StructureClass
from ipsurvey.domain.detection.ground import ground_estimate
from ipsurvey.domain.extraction.fusion import FusedField, fuse
from ipsurvey.domain.extraction.road import estimate_road
from ipsurvey.domain.extraction.street import StreetEstimate, assign_poles, street_estimate

EARTH_R = 6_371_008.8
RAIO_M = 200.0  # entorno de cada captura para cadastro e mapa
RAIO_MAPA_M = 120.0  # postes do cadastro levados ao mapa da interface


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


def bbox(lat: float, lon: float, r: float) -> tuple[float, float, float, float]:
    dlat = math.degrees(r / EARTH_R)
    dlon = dlat / math.cos(math.radians(lat))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def campo_json(f: FusedField) -> dict:
    return {
        "coluna": f.column,
        "rotulo": f.label,
        "valor": f.value,
        "unidade": f.unit if f.value is not None else "",
        "estado": "estimado" if f.value is not None else "pendente",
        "fonte": f.source,
        "metodo": f.method,
        "divergente": f.divergent,
        "candidatos": [
            {"fonte": c.source, "valor": c.value, "detalhe": c.detail} for c in f.candidates
        ],
    }


def via_da_captura(
    lat: float, lon: float, ways: list[RoadWay], frame: LocalFrame
) -> RoadWay | None:
    """A via em que a câmera está: o eixo mais próximo (até 25 m), fora vias de serviço."""
    melhor: tuple[float, RoadWay] | None = None
    p = frame.to_xy(lat, lon)
    for w in ways:
        if w.highway == "service":
            continue
        d = abs(linear_ref(p, [frame.to_xy(a, b) for a, b in w.coords]).offset_m)
        if d <= 25 and (melhor is None or d < melhor[0]):
            melhor = (d, w)
    return melhor[1] if melhor else None


def moda(xs: list) -> object | None:
    xs = [x for x in xs if x is not None]
    return collections.Counter(xs).most_common(1)[0][0] if xs else None


def main() -> None:  # noqa: PLR0915 (roteiro de exportação, linear de propósito)
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("dataset")
    ap.add_argument("--camera-height", type=float, default=1.9)
    ap.add_argument("--min-pole-height", type=float, default=4.0)
    ap.add_argument("--width", type=int, default=2048, help="largura das imagens exportadas")
    ap.add_argument(
        "--bdgd-dir", default=os.environ.get("IPSURVEY_BDGD_DIR"), help="parquets do Ignis"
    )
    ap.add_argument("--sem-mapa", action="store_true", help="não consulta o OSM")
    args = ap.parse_args()

    m = load_manifest(args.dataset)
    src = ROOT / m["local_dir"]
    cache_dir = ROOT / "data/eval/owlv2" / args.dataset
    out = ROOT / "web/public/demo"
    (out / "img").mkdir(parents=True, exist_ok=True)
    post = PostProcess()

    cadastro = BdgdParquetCadastre(args.bdgd_dir) if args.bdgd_dir else None
    com_cadastro = cadastro.available() if cadastro else set()
    itens = [it for it in m["items"] if (cache_dir / (Path(it["file"]).stem + ".json")).exists()]
    ways_todas: list[RoadWay] = []
    if not args.sem_mapa:
        ways_todas = OverpassRoads(ROOT / "data/osm").ways_around(
            [(it["lat"], it["lon"]) for it in itens], RAIO_M
        )
        print(f"OSM: {len(ways_todas)} vias no entorno das capturas")

    capturas: list[dict] = []
    postes_mapa: dict[str, dict] = {}
    for it in itens:
        cache = json.loads((cache_dir / (Path(it["file"]).stem + ".json")).read_text("utf-8"))
        dets = [
            d
            for d in angular_from_cache(cache, post)
            if not is_low_pole(d, args.camera_height, args.min_pole_height)
            and not is_tall_luminaire(d)
        ]
        travel = it.get("travel_bearing_deg")
        travel_az = math.radians(travel - it["heading_deg"]) if travel is not None else 0.0
        road = estimate_road(dets, args.camera_height, travel_az)
        planta = {p.index: p for p in road.poles}
        frame = LocalFrame(it["lat"], it["lon"])

        # ---- mapa e cadastro no entorno
        s, w, n, e = bbox(it["lat"], it["lon"], RAIO_M)
        ways = [
            wy for wy in ways_todas if any(s <= la <= n and w <= lo <= e for la, lo in wy.coords)
        ]
        via = via_da_captura(it["lat"], it["lon"], ways, frame)
        poles: list[CadastrePole] = []
        if cadastro and it.get("ibge") in com_cadastro:
            poles = group_poles(cadastro.points_in_bbox(it["ibge"], s, w, n, e))
        rua: StreetEstimate | None = None
        if via is not None and poles:
            rua = street_estimate(via, assign_poles(ways, poles, frame)[via.way_id])

        # ---- detecções (com posição) e casamento com o cadastro
        deteccoes = []
        for k, d in enumerate(dets):
            est = ground_estimate(d, args.camera_height) if d.cls is StructureClass.POLE else None
            lat = lon = None
            if est is not None:
                lat, lon = destination(
                    it["lat"],
                    it["lon"],
                    it["heading_deg"] + math.degrees(d.az_center),
                    est.distance_m,
                )
            pl = planta.get(k)
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
                    "planta": {"x": round(pl.x_m, 2), "y": round(pl.y_m, 2), "lado": pl.side.value}
                    if pl
                    else None,
                }
            )
        # Casamento poste a poste (imagem × BDGD) fica de fora: no golden ele não supera o
        # acaso (GPS da câmera + estimativa de um quadro + coordenada esquemática da BDGD).
        # Volta com triangulação entre quadros e GNSS RTK. Ver docs/algorithms/fusao-fontes.md.
        for p in poles:
            if math.dist(frame.to_xy(p.lat, p.lon), (0, 0)) > RAIO_MAPA_M:
                continue
            postes_mapa.setdefault(
                p.pole_id,
                {
                    "id": p.pole_id,
                    "lat": round(p.lat, 7),
                    "lon": round(p.lon, 7),
                    "luminarias": p.n_luminaires,
                    "tecnologia": moda([q.technology for q in p.points]),
                    "potenciaW": moda([q.power_w for q in p.points]),
                },
            )

        img_name = Path(it["file"]).stem + ".jpg"
        if not (out / "img" / img_name).exists():
            im = Image.open(src / it["file"]).convert("RGB")
            im.resize((args.width, args.width // 2), Image.Resampling.LANCZOS).save(
                out / "img" / img_name, quality=82, optimize=True
            )

        campos = fuse(road, rua, via)
        capturas.append(
            {
                "id": it["id"],
                "arquivo": it["file"],
                "imagem": f"demo/img/{img_name}",
                "cidade": it["city"],
                "lat": it["lat"],
                "lon": it["lon"],
                "rumo": it["heading_deg"],
                "rumoDeslocamento": travel,
                "data": it["captured"],
                "camera": it["camera"],
                "autor": it["author"],
                "licenca": it["license"],
                "origem": f"https://api.panoramax.xyz/#focus=pic&pic={it['id']}",
                "deteccoes": deteccoes,
                "via": {
                    "postesNoPlano": len(road.poles),
                    "larguraAlinhamentosM": round(road.alignment_width_m, 1)
                    if road.alignment_width_m
                    else None,
                    "logradouro": via.name if via else None,
                    "classeOsm": via.highway if via else None,
                    "maoUnica": via.oneway if via else None,
                    "postesCadastroNaVia": len(rua.poles) if rua else 0,
                    "tecnologia": moda([q.technology for sp in rua.poles for q in sp.pole.points])
                    if rua
                    else None,
                    "potenciaW": moda([q.power_w for sp in rua.poles for q in sp.pole.points])
                    if rua
                    else None,
                    "campos": [campo_json(f) for f in campos],
                },
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
        "fontesCadastro": "BDGD/ANEEL (cadastro derivado pelo Ignis)" if cadastro else None,
        "parametros": {
            "alturaCameraM": args.camera_height,
            "alturaMinimaPosteM": args.min_pole_height,
            "limiares": {c.value: v for c, v in DEFAULT_THRESHOLDS.items()},
            "descricoes": {c.value: list(v) for c, v in DEFAULT_PROMPTS.items()},
        },
        "cadastro": list(postes_mapa.values()),
        "capturas": capturas,
    }
    (out / f"campanha-{args.dataset}.json").write_text(
        json.dumps(campanha, ensure_ascii=False), "utf-8"
    )
    resumo = {k: campanha[k] for k in ("id", "nome", "municipio", "status", "criadaEm", "modelo")}
    resumo["capturas"] = len(capturas)
    resumo["postes"] = sum(d["classe"] == "poste" for c in capturas for d in c["deteccoes"])
    (out / "campanhas.json").write_text(json.dumps([resumo], ensure_ascii=False), "utf-8")
    print(f"{out}: {len(capturas)} capturas, {resumo['postes']} postes detectados")
    print(f"BDGD: {len(postes_mapa)} postes do cadastro no entorno das capturas")


if __name__ == "__main__":
    main()
