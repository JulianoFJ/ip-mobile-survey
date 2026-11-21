"""Baixa um golden dataset a partir do manifesto em benchmarks/golden/<nome>.yaml.

Uso:
    uv run python scripts/fetch_datasets.py panoramax-br-v0
    uv run python scripts/fetch_datasets.py panoramax-br-v0 --verify   # só confere hashes

Os arquivos vão para o `local_dir` do manifesto (dentro de data/, fora do git).
Arquivos já presentes e com hash correto não são baixados de novo.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "benchmarks" / "golden"
USER_AGENT = "ip-mobile-survey/fetch_datasets"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(item: dict, out_dir: Path, client: httpx.Client, verify_only: bool) -> str:
    dest = out_dir / item["file"]
    if dest.exists() and sha256(dest) == item["sha256"]:
        return "ok"
    if verify_only:
        return "ausente" if not dest.exists() else "hash divergente"
    tmp = dest.with_suffix(dest.suffix + ".part")
    with client.stream("GET", item["uri"]) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
    if sha256(tmp) != item["sha256"]:
        tmp.unlink()
        return "hash divergente após download"
    tmp.replace(dest)
    return "baixado"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("dataset", help="nome do manifesto, sem .yaml")
    ap.add_argument("--verify", action="store_true", help="não baixa, só confere os hashes")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    manifest = yaml.safe_load((GOLDEN / f"{args.dataset}.yaml").read_text(encoding="utf-8"))
    out_dir = ROOT / manifest["local_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    items = manifest["items"]

    headers = {"User-Agent": USER_AGENT}
    with (
        httpx.Client(headers=headers, timeout=120, follow_redirects=True) as client,
        ThreadPoolExecutor(args.workers) as ex,
    ):
        results = list(ex.map(lambda it: fetch(it, out_dir, client, args.verify), items))

    pairs = zip(items, results, strict=True)
    failed = [(it["file"], st) for it, st in pairs if st not in ("ok", "baixado")]
    ok = len(items) - len(failed)
    print(f"{manifest['name']}: {ok}/{len(items)} arquivos íntegros em {out_dir}")
    print(f"Licença: {manifest['license']}. {manifest['attribution']}")
    for name, st in failed:
        print(f"  FALHA {name}: {st}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
