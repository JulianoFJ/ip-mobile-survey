"""Avaliação visual do detector zero-shot num golden dataset.

    uv run --extra vision python scripts/eval_zero_shot.py run panoramax-br-v0
    uv run --extra vision python scripts/eval_zero_shot.py render panoramax-br-v0

`run` roda o OWLv2 nas 16 vistas de cada panorama e guarda as caixas brutas em
data/eval/owlv2/<dataset>/ (uma vez só; é a parte lenta). `render` aplica o
pós-processamento, junta as detecções em ângulos e gera uma galeria HTML com as caixas
desenhadas no panorama. Para testar outros limiares, rode só o `render`.
"""

from __future__ import annotations

import argparse
import html
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

from ipsurvey.adapters.detection.owlv2 import DEFAULT_THRESHOLDS, PostProcess, RawBox
from ipsurvey.domain.detection import AngularDetection, StructureClass, merge_detections, to_angular
from ipsurvey.domain.detection.ground import ground_estimate
from ipsurvey.domain.geometry.perspective import equirect_angles_to_pixel, view_ring

ROOT = Path(__file__).resolve().parent.parent
COLORS = {
    StructureClass.POLE: (255, 140, 0),
    StructureClass.LUMINAIRE: (0, 230, 120),
    StructureClass.ARM: (0, 190, 255),
}


def load_manifest(name: str) -> dict:
    return yaml.safe_load((ROOT / "benchmarks/golden" / f"{name}.yaml").read_text("utf-8"))


def cmd_run(args: argparse.Namespace) -> None:
    from ipsurvey.adapters.detection.owlv2 import Owlv2Detector
    from ipsurvey.domain.geometry.perspective import render_view

    m = load_manifest(args.dataset)
    src = ROOT / m["local_dir"]
    out = ROOT / "data/eval/owlv2" / args.dataset
    out.mkdir(parents=True, exist_ok=True)
    det = Owlv2Detector()
    views = view_ring()
    items = m["items"][: args.limit] if args.limit else m["items"]
    for n, it in enumerate(items, 1):
        dest = out / (Path(it["file"]).stem + ".json")
        if dest.exists():
            continue
        t = time.time()
        pano = np.asarray(Image.open(src / it["file"]).convert("RGB"))
        per_view = []
        for i, v in enumerate(views):
            raw = det.detect_raw(render_view(pano, v))
            per_view.append({"view": i, "boxes": [{**asdict(r), "cls": r.cls.value} for r in raw]})
        dest.write_text(
            json.dumps({"file": it["file"], "model": det.model_id, "views": per_view}), "utf-8"
        )
        print(f"[{n}/{len(items)}] {it['file']} {time.time() - t:.1f}s", flush=True)


def angular_from_cache(
    cache: dict, post: PostProcess, drop_prompts: set[str] = frozenset()
) -> list[AngularDetection]:
    views = view_ring()
    found: list[AngularDetection] = []
    for pv in cache["views"]:
        v = views[pv["view"]]
        raw = [
            RawBox(**{**b, "cls": StructureClass(b["cls"])})
            for b in pv["boxes"]
            if b.get("prompt", "") not in drop_prompts
        ]
        found.extend(to_angular(d, v, view_index=pv["view"]) for d in post(raw, v.width, v.height))
    return merge_detections(found)


def label(det: AngularDetection, camera_height: float) -> str:
    if det.cls is not StructureClass.POLE:
        return f"{det.score:.2f}"
    est = ground_estimate(det, camera_height)
    if est is None:
        return f"{det.score:.2f}"
    sign = "≥" if est.height_is_lower_bound else ""
    return f"{det.score:.2f} · {sign}{est.height_m:.1f} m @ {est.distance_m:.0f} m"


def is_low_pole(det: AngularDetection, camera_height: float, min_height: float) -> bool:
    """Poste com pé visível e altura estimada abaixo do mínimo (placa, haste, sinal)."""
    if det.cls is not StructureClass.POLE:
        return False
    est = ground_estimate(det, camera_height)
    return est is not None and not est.height_is_lower_bound and est.height_m < min_height


def is_tall_luminaire(det: AngularDetection, max_aspect: float = 2.0) -> bool:
    """Luminária que, depois de juntar as vistas, ficou alta como um poste."""
    if det.cls is not StructureClass.LUMINAIRE or det.az_half_width <= 0:
        return False
    return (det.el_max - det.el_min) / det.az_width > max_aspect


def draw(pano: Image.Image, dets: list[AngularDetection], camera_height: float) -> Image.Image:
    img = pano.copy()
    w, h = img.size
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=max(12, w // 120))
    for det in sorted(dets, key=lambda x: x.cls != StructureClass.POLE):
        u0, v0 = equirect_angles_to_pixel(det.az_center - det.az_half_width, det.el_max, w, h)
        u1, v1 = equirect_angles_to_pixel(det.az_center + det.az_half_width, det.el_min, w, h)
        u0, u1, v0, v1 = float(u0), float(u1), float(v0), float(v1)
        spans = [(u0, u1)] if u1 >= u0 else [(u0, w - 1.0), (0.0, u1)]  # atravessa ±180°
        color = COLORS[det.cls]
        lw = max(2, w // 700)
        for a, b in spans:
            d.rectangle([a, v0, max(b, a + 2), v1], outline=color, width=lw)
        d.text((u0 + 3, v0 - font.size - 2), label(det, camera_height), fill=color, font=font)
    return img


def cmd_render(args: argparse.Namespace) -> None:
    m = load_manifest(args.dataset)
    src = ROOT / m["local_dir"]
    cache_dir = ROOT / "data/eval/owlv2" / args.dataset
    out = ROOT / "data/eval/owlv2" / f"{args.dataset}-galeria"
    out.mkdir(parents=True, exist_ok=True)
    thr = dict(DEFAULT_THRESHOLDS)
    for spec in args.thr or []:
        k, val = spec.split("=")
        thr[StructureClass(k)] = float(val)
    post = PostProcess(thresholds=thr)
    cards, totals = [], dict.fromkeys(StructureClass, 0)
    for it in m["items"]:
        cpath = cache_dir / (Path(it["file"]).stem + ".json")
        if not cpath.exists():
            continue
        dets = angular_from_cache(
            json.loads(cpath.read_text("utf-8")), post, set(args.drop_prompt or [])
        )
        dets = [
            d
            for d in dets
            if not is_low_pole(d, args.camera_height, args.min_pole_height)
            and not is_tall_luminaire(d)
        ]
        pano = Image.open(src / it["file"]).convert("RGB")
        pano = pano.resize((args.width, args.width // 2), Image.Resampling.LANCZOS)
        name = Path(it["file"]).stem + ".jpg"
        draw(pano, dets, args.camera_height).save(out / name, quality=85)
        counts = {c: sum(d.cls is c for d in dets) for c in StructureClass}
        for c, k in counts.items():
            totals[c] += k
        summary = " · ".join(f"{k} {c.value}" for c, k in counts.items())
        link = f"https://api.panoramax.xyz/#focus=pic&pic={it['id']}"
        cards.append(
            f'<figure><a href="{name}"><img src="{name}" loading="lazy"></a>'
            f"<figcaption><b>{html.escape(it['city'])}</b> · {summary} · "
            f'<a href="{link}">{html.escape(it["author"])}, CC BY-SA 4.0</a></figcaption></figure>'
        )
    legend = " ".join(
        f'<span style="color:rgb{COLORS[c]}">■ {c.value} (≥ {thr[c]:.2f})</span>'
        for c in StructureClass
    )
    page = f"""<!doctype html><meta charset="utf-8"><title>OWLv2 · {args.dataset}</title>
<style>body{{font:14px system-ui;margin:16px;background:#111;color:#ddd}}
figure{{margin:0 0 24px}}img{{width:100%;height:auto}}a{{color:#9cf}}</style>
<h1>OWLv2 zero-shot · {args.dataset}</h1><p>{legend}</p>
<p>Postes: confiança · altura estimada @ distância (chão plano, câmera a {args.camera_height} m).
Descartados os postes com pé visível e menos de {args.min_pole_height} m.</p>
<p>{len(cards)} panoramas · {" · ".join(f"{k} {c.value}" for c, k in totals.items())}</p>
{"".join(cards)}"""
    (out / "index.html").write_text(page, "utf-8")
    print(f"{out / 'index.html'}  ({len(cards)} panoramas, {totals})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(required=True)
    r = sub.add_parser("run")
    r.add_argument("dataset")
    r.add_argument("--limit", type=int, default=0)
    r.set_defaults(fn=cmd_run)
    g = sub.add_parser("render")
    g.add_argument("dataset")
    g.add_argument("--width", type=int, default=2880)
    g.add_argument("--thr", nargs="*", help="ex.: poste=0.3 luminaria=0.2")
    g.add_argument("--drop-prompt", nargs="*", help="descrições a ignorar")
    g.add_argument("--camera-height", type=float, default=1.9, help="m sobre o chão")
    g.add_argument("--min-pole-height", type=float, default=4.0, help="m")
    g.set_defaults(fn=cmd_render)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
