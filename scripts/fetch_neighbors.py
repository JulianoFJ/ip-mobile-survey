"""Baixa as fotos vizinhas (anterior e seguinte na sequência) de cada captura do golden.

    uv run python scripts/fetch_neighbors.py panoramax-br-v0

Grava as imagens em data/golden/<dataset>-vizinhos/ e o manifesto
benchmarks/golden/<dataset>-vizinhos.yaml (mesmo formato do golden, com `vizinho_de`
e `deslocamento` = -1 ou +1). É o que a triangulação entre quadros precisa: o mesmo poste
visto de duas ou três posições.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
import time
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.panoramax.xyz/api"


def bearing(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    y = math.sin(lo2 - lo1) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset")
    args = ap.parse_args()
    m = yaml.safe_load((ROOT / "benchmarks/golden" / f"{args.dataset}.yaml").read_text("utf-8"))
    nome = f"{args.dataset}-vizinhos"
    out = ROOT / "data/golden" / nome
    out.mkdir(parents=True, exist_ok=True)
    itens = []
    with httpx.Client(headers={"User-Agent": "ip-mobile-survey/vizinhos"}, timeout=120) as c:
        for it in m["items"]:
            centro = c.get(f"{API}/collections/{it['collection']}/items/{it['id']}").json()
            for link in centro["links"]:
                if link["rel"] not in ("prev", "next"):
                    continue
                viz = c.get(link["href"]).json()
                lon, lat = viz["geometry"]["coordinates"]
                p = viz["properties"]
                lado = "ant" if link["rel"] == "prev" else "seg"
                fn = f"{Path(it['file']).stem}_{lado}_{viz['id'][:8]}.jpg"
                dest = out / fn
                if not dest.exists():
                    tmp = dest.with_suffix(".part")
                    with c.stream("GET", viz["assets"]["hd"]["href"]) as r:
                        r.raise_for_status()
                        with tmp.open("wb") as f:
                            for chunk in r.iter_bytes(1 << 20):
                                f.write(chunk)
                    tmp.replace(dest)
                io = p.get("pers:interior_orientation", {})
                itens.append(
                    {
                        "file": fn,
                        "id": viz["id"],
                        "collection": it["collection"],
                        "vizinho_de": it["id"],
                        "deslocamento": -1 if link["rel"] == "prev" else 1,
                        "city": it["city"],
                        "ibge": it.get("ibge"),
                        "lat": round(lat, 7),
                        "lon": round(lon, 7),
                        "captured": p["datetime"][:19],
                        "heading_deg": p.get("view:azimuth"),
                        "camera": (
                            io.get("camera_manufacturer", "") + " " + io.get("camera_model", "")
                        )
                        .strip()
                        .replace("GoPro GoPro", "GoPro"),
                        "author": p.get("geovisio:producer"),
                        "license": p.get("license"),
                        "uri": viz["assets"]["hd"]["href"],
                        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                        "bytes": dest.stat().st_size,
                        "distancia_ao_centro_m": round(
                            6_371_008.8
                            * math.radians(1)
                            * math.hypot(
                                lat - it["lat"], (lon - it["lon"]) * math.cos(math.radians(lat))
                            ),
                            1,
                        ),
                        "rumo_ao_centro_deg": round(bearing((lat, lon), (it["lat"], it["lon"])), 1),
                    }
                )
                time.sleep(0.1)
            print(
                f"{it['file']}: {sum(1 for x in itens if x['vizinho_de'] == it['id'])} vizinhos",
                flush=True,
            )
    man = {
        "name": nome,
        "description": (
            f"Fotos vizinhas (anterior e seguinte na sequência) das capturas de {args.dataset}, "
            "para triangulação."
        ),
        "source": m["source"],
        "license": m["license"],
        "attribution": m["attribution"],
        "retrieved": time.strftime("%Y-%m-%d"),
        "local_dir": f"data/golden/{nome}",
        "items": itens,
    }
    (ROOT / "benchmarks/golden" / f"{nome}.yaml").write_text(
        "# Gerado por scripts/fetch_neighbors.py\n"
        + yaml.safe_dump(man, allow_unicode=True, sort_keys=False, width=120),
        "utf-8",
    )
    print(f"{len(itens)} vizinhos em {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
