"""Malha viária do OpenStreetMap pela Overpass API, com cache em disco.

Dados © contribuidores do OpenStreetMap, licença ODbL. Uso interno de análise; se uma
base derivada for distribuída, vale a atribuição e o compartilhamento pela mesma licença.
"""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import httpx

from ipsurvey.domain.cadastre import RoadWay

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
#: Vias por onde passa carro e que recebem IP de via pública.
HIGHWAYS = (
    "motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|service"
)


def _int(v: str | None) -> int | None:
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None


class OverpassRoads:
    """Implementa a porta `RoadNetworkSource`."""

    def __init__(
        self, cache_dir: str | Path, url: str = OVERPASS_URL, timeout_s: float = 180
    ) -> None:
        """Recebe a pasta de cache (uma consulta igual não vai à rede de novo)."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.url = url
        self.timeout_s = timeout_s

    def _query(self, q: str) -> dict:
        key = hashlib.sha256(q.encode()).hexdigest()[:24]
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text("utf-8"))
        r = httpx.post(
            self.url,
            data={"data": q},
            headers={"User-Agent": "ip-mobile-survey/roads"},
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        tmp = path.with_suffix(".part")
        tmp.write_text(json.dumps(data), "utf-8")
        tmp.replace(path)
        return data

    def ways_around(self, points: Sequence[tuple[float, float]], radius_m: float) -> list[RoadWay]:
        """Vias a até `radius_m` de qualquer um dos pontos, com geometria e atributos."""
        partes = "".join(
            f'way(around:{radius_m:.0f},{lat:.6f},{lon:.6f})["highway"~"^({HIGHWAYS})$"];'
            for lat, lon in points
        )
        data = self._query(f"[out:json][timeout:{int(self.timeout_s)}];({partes});out geom tags;")
        out: list[RoadWay] = []
        for el in data.get("elements", []):
            geom = el.get("geometry") or []
            if el.get("type") != "way" or len(geom) < 2:
                continue
            tags = el.get("tags", {})
            out.append(
                RoadWay(
                    way_id=f"osm:{el['id']}",
                    coords=tuple((g["lat"], g["lon"]) for g in geom),
                    highway=tags.get("highway", ""),
                    name=tags.get("name"),
                    lanes=_int(tags.get("lanes")),
                    oneway=tags.get("oneway") in {"yes", "1", "true"},
                    tags=tags,
                )
            )
        return out
