"""Larguras da via por segmentação do chão, no golden dataset.

    uv run --extra vision python scripts/eval_cross_section.py run panoramax-br-v0 [--limit N]
    uv run --extra vision python scripts/eval_cross_section.py orientar panoramax-br-v0
    uv run --extra vision python scripts/eval_cross_section.py plantas panoramax-br-v0

`run` segmenta as 8 vistas de chão de cada panorama com o OneFormer e guarda os rótulos em
data/eval/seg/<dataset>/<arquivo>.npz (uma vez só; ~12 s por panorama). `orientar` mede o
eixo da pista em cada panorama e decide para que lado do panorama está a frente do veículo
(data/eval/seg/<dataset>/orientacao.json). `plantas` monta a
planta vista de cima (imagem do chão + rótulos + bordas medidas) de cada panorama, para
conferir o corte transversal a olho.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

import numpy as np
from eval_zero_shot import ROOT, load_manifest
from PIL import Image, ImageDraw, ImageFont

from ipsurvey.domain.extraction.cross_section import (
    CrossSection,
    GroundClass,
    GroundGrid,
    cross_section,
    front_from_axis,
    ground_grid,
    ground_views,
    road_axis,
)
from ipsurvey.domain.geometry.perspective import equirect_angles_to_pixel

CORES = {
    GroundClass.OTHER: (60, 60, 60),
    GroundClass.ROAD: (230, 110, 150),
    GroundClass.SIDEWALK: (240, 200, 60),
    GroundClass.VEGETATION: (60, 190, 90),
    GroundClass.VEHICLE: (70, 120, 230),
}


def cache_dir(dataset: str) -> Path:
    return ROOT / "data/eval/seg" / dataset


#: Para que lado do panorama a frente do veículo costuma estar, por câmera. Só desempata
#: o sentido do eixo da pista (que vem sem sentido). Na GoPro Max presa no teto do golden,
#: o para-brisa aparece a +90° do centro da imagem.
FRENTE_ESPERADA_DEG = {"GoPro Max": 90.0}
ANISOTROPIA_MIN = 2.0


def orientacao_path(dataset: str) -> Path:
    return cache_dir(dataset) / "orientacao.json"


def ler_orientacao(dataset: str) -> dict[str, dict]:
    p = orientacao_path(dataset)
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def travel_az(it: dict, orient: dict[str, dict] | None = None) -> float:
    """Azimute do panorama (rad) que aponta para a frente do veículo."""
    o = (orient or {}).get(it["id"])
    if o is not None:
        return math.radians(o["frente_deg"])
    return math.radians(FRENTE_ESPERADA_DEG.get(it["camera"], 0.0))


def carregar_grade(
    it: dict, dataset: str, camera_height: float, taz: float, cell: float = 0.1
) -> GroundGrid | None:
    p = cache_dir(dataset) / (Path(it["file"]).stem + ".npz")
    if not p.exists():
        return None
    labels = list(np.load(p)["labels"])
    views = ground_views(size=labels[0].shape[0])
    return ground_grid(labels, views, camera_height, taz, cell_m=cell)


def medir(
    it: dict, dataset: str, camera_height: float, orient: dict[str, dict]
) -> CrossSection | None:
    g = carregar_grade(it, dataset, camera_height, travel_az(it, orient))
    return cross_section(g) if g is not None else None


def cmd_orientar(args: argparse.Namespace) -> None:
    m = load_manifest(args.dataset)
    res: dict[str, dict] = {}
    for it in m["items"]:
        g = carregar_grade(it, args.dataset, args.camera_height, 0.0, cell=0.2)
        if g is None:
            continue
        ax = road_axis(g)
        esperado = math.radians(FRENTE_ESPERADA_DEG.get(it["camera"], 0.0))
        if ax is not None and ax.anisotropy >= ANISOTROPIA_MIN:
            frente, fonte = front_from_axis(ax.az, esperado), "eixo da pista"
        else:
            frente, fonte = esperado, "padrão da câmera"
        res[it["id"]] = {
            "eixo_deg": round(math.degrees(ax.az), 1) if ax else None,
            "anisotropia": round(ax.anisotropy, 2) if ax else None,
            "frente_deg": round(math.degrees(frente), 1),
            "fonte": fonte,
        }
    orientacao_path(args.dataset).write_text(json.dumps(res, indent=1), "utf-8")
    por_cam: dict[str, list[float]] = {}
    for it in m["items"]:
        o = res.get(it["id"])
        if o and o["fonte"] == "eixo da pista":
            por_cam.setdefault(it["camera"], []).append(o["frente_deg"])
    n_eixo = sum(o["fonte"] == "eixo da pista" for o in res.values())
    print(f"{len(res)} panoramas; frente pelo eixo da pista em {n_eixo}")
    for cam, fs in por_cam.items():
        med = statistics.median(fs)
        print(f"  {cam}: n={len(fs)} frente mediana {med:.0f}° (de {min(fs):.0f} a {max(fs):.0f})")


def cmd_run(args: argparse.Namespace) -> None:
    from ipsurvey.adapters.segmentation.oneformer import OneFormerGroundSegmenter
    from ipsurvey.domain.geometry.perspective import render_view

    m = load_manifest(args.dataset)
    out = cache_dir(args.dataset)
    out.mkdir(parents=True, exist_ok=True)
    seg = OneFormerGroundSegmenter()
    views = ground_views()
    items = m["items"][: args.limit] if args.limit else m["items"]
    for n, it in enumerate(items, 1):
        dest = out / (Path(it["file"]).stem + ".npz")
        if dest.exists():
            continue
        t = time.time()
        pano = np.asarray(Image.open(ROOT / m["local_dir"] / it["file"]).convert("RGB"))
        labels = np.stack([seg.segment(render_view(pano, v)) for v in views])
        np.savez_compressed(dest, labels=labels)
        print(f"[{n}/{len(items)}] {it['file']} {time.time() - t:.1f}s", flush=True)


def planta_rgb(pano: np.ndarray, g: GroundGrid, camera_height: float, taz: float) -> np.ndarray:
    gx, gy = np.meshgrid(g.xs, g.ys)
    az = np.arctan2(gx, gy) + taz
    el = -np.arctan2(camera_height, np.maximum(np.hypot(gx, gy), 1e-6))
    h, w = pano.shape[:2]
    u, v = equirect_angles_to_pixel(az, el, w, h)
    return pano[np.clip(v.astype(int), 0, h - 1), np.clip(u.astype(int), 0, w - 1)]


def cmd_plantas(args: argparse.Namespace) -> None:
    m = load_manifest(args.dataset)
    out = ROOT / "data/eval/seg" / f"{args.dataset}-plantas"
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=14)
    feitas = 0
    orient = ler_orientacao(args.dataset)
    for it in m["items"]:
        taz = travel_az(it, orient)
        g = carregar_grade(it, args.dataset, args.camera_height, taz)
        if g is None:
            continue
        cs = cross_section(g)
        pano = np.asarray(Image.open(ROOT / m["local_dir"] / it["file"]).convert("RGB"))
        rgb = planta_rgb(pano, g, args.camera_height, taz)[::-1]  # y para cima
        lab = np.array([CORES[GroundClass(c)] for c in range(5)], np.uint8)[g.labels][::-1]
        mix = (0.55 * rgb + 0.45 * lab).astype(np.uint8)
        img = Image.fromarray(np.hstack([rgb, mix]))
        d = ImageDraw.Draw(img)
        w0 = rgb.shape[1]
        cell = g.cell_m

        def col(x: float, x0: float = float(g.xs[0]), c: float = cell) -> float:
            return (x - x0) / c

        y0, y1 = (g.ys[-1] - 10.0) / cell, (g.ys[-1] + 6.0) / cell  # janela de medida
        for off in (0, w0):
            d.rectangle([off, y0, off + w0 - 1, y1], outline=(255, 255, 255))
            if cs.curb_left_m is not None:
                d.line(
                    [off + col(-cs.curb_left_m), 0, off + col(-cs.curb_left_m), img.height],
                    fill=(0, 255, 255),
                    width=2,
                )
            if cs.curb_right_m is not None:
                d.line(
                    [off + col(cs.curb_right_m), 0, off + col(cs.curb_right_m), img.height],
                    fill=(0, 255, 255),
                    width=2,
                )
        txt = (
            f"{it['city']} | pista {cs.road_width_m or 0:.1f} m | passeios "
            f"{cs.sidewalk_left_m or 0:.1f}/{cs.sidewalk_right_m or 0:.1f} m | canteiro "
            f"{cs.median_m or 0:.1f} m | fatias {cs.rows_used}/{cs.rows_total}"
        )
        d.rectangle([0, 0, img.width, 20], fill=(0, 0, 0))
        d.text((6, 3), txt, fill=(255, 255, 255), font=font)
        img.save(out / (Path(it["file"]).stem + ".jpg"), quality=85)
        feitas += 1
    print(f"{out}: {feitas} plantas")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(required=True)
    r = sub.add_parser("run")
    r.add_argument("dataset")
    r.add_argument("--limit", type=int, default=0)
    r.set_defaults(fn=cmd_run)
    o = sub.add_parser("orientar")
    o.add_argument("dataset")
    o.add_argument("--camera-height", type=float, default=1.9)
    o.set_defaults(fn=cmd_orientar)
    p = sub.add_parser("plantas")
    p.add_argument("dataset")
    p.add_argument("--camera-height", type=float, default=1.9)
    p.set_defaults(fn=cmd_plantas)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
