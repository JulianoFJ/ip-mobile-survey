"""Cadastro de IP derivado da BDGD da ANEEL, no formato publicado pelo Ignis.

O Ignis (Plataforma IP, `cadastro_bdgd/`) extrai da BDGD o cadastro ponto a ponto de cada
município (PIP + coordenada do poste no PONNOT) e publica um parquet por código IBGE em
`cadastro_bdgd/data/cadastros/<ibge>.parquet`. Este adaptador lê esses arquivos; não vai à
ANEEL. A pasta é configurável (`IPSURVEY_BDGD_DIR`), para apontar para o clone do Ignis
ou para uma cópia.

Colunas usadas: id_ponto, latitude, longitude, tecnologia, potencia_lampada_w,
area_urbana. A coordenada é a do **poste da rede**, não a da luminária.
"""

from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

from ipsurvey.domain.cadastre import CadastrePoint


class BdgdParquetCadastre:
    """Implementa a porta `CadastreSource` sobre os parquets do Ignis."""

    def __init__(self, directory: str | Path) -> None:
        """Recebe a pasta com os `<ibge>.parquet`."""
        self.directory = Path(directory)

    def available(self) -> set[str]:
        """Códigos IBGE com cadastro publicado."""
        return {p.stem for p in self.directory.glob("*.parquet")}

    def points_in_bbox(
        self, ibge: str, south: float, west: float, north: float, east: float
    ) -> list[CadastrePoint]:
        """Pontos do município dentro do retângulo."""
        path = self.directory / f"{ibge}.parquet"
        if not path.exists():
            msg = f"sem cadastro BDGD publicado para o município {ibge} em {self.directory}"
            raise FileNotFoundError(msg)
        t = pq.read_table(
            path,
            columns=[
                "id_ponto",
                "latitude",
                "longitude",
                "tecnologia",
                "potencia_lampada_w",
                "area_urbana",
            ],
        )
        lat, lon = t["latitude"], t["longitude"]
        mask = pc.and_(
            pc.and_(pc.greater_equal(lat, south), pc.less_equal(lat, north)),
            pc.and_(pc.greater_equal(lon, west), pc.less_equal(lon, east)),
        )
        rows = t.filter(mask).to_pylist()
        return [
            CadastrePoint(
                point_id=str(r["id_ponto"]),
                lat=float(r["latitude"]),
                lon=float(r["longitude"]),
                technology=str(r["tecnologia"]) if r["tecnologia"] is not None else None,
                power_w=float(r["potencia_lampada_w"])
                if r["potencia_lampada_w"] is not None
                else None,
                urban=bool(r["area_urbana"]) if r["area_urbana"] is not None else None,
            )
            for r in rows
        ]
