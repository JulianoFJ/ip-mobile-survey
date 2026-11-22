"""Cadastro de IP derivado da BDGD da ANEEL, no formato publicado pelo Ignis.

O Ignis (Plataforma IP, `cadastro_bdgd/`) extrai da BDGD o cadastro ponto a ponto de cada
município (PIP + coordenada do poste no PONNOT) e publica um parquet por código IBGE em
`cadastro_bdgd/data/cadastros/<ibge>.parquet` (os de trabalho local ficam em
`dados/bdgd/cadastros/`). Este adaptador lê esses arquivos; não vai à ANEEL. Aceita várias
pastas, procuradas em ordem (`IPSURVEY_BDGD_DIR`, separadas por `:`).

Colunas usadas: id_ponto, latitude, longitude, tecnologia, potencia_lampada_w,
area_urbana. A coordenada é a do **poste da rede**, não a da luminária.
"""

import os
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ipsurvey.domain.cadastre import CadastrePoint


class BdgdParquetCadastre:
    """Implementa a porta `CadastreSource` sobre os parquets do Ignis."""

    def __init__(self, directories: str | Path | list[str | Path]) -> None:
        """Recebe a pasta (ou as pastas, em ordem de preferência) com os `<ibge>.parquet`."""
        if isinstance(directories, str):
            directories = [d for d in directories.split(os.pathsep) if d]
        elif isinstance(directories, Path):
            directories = [directories]
        self.directories = [Path(d) for d in directories]

    def available(self) -> set[str]:
        """Códigos IBGE com cadastro em alguma das pastas."""
        return {p.stem for d in self.directories for p in d.glob("*.parquet")}

    def _path(self, ibge: str) -> Path | None:
        return next(
            (d / f"{ibge}.parquet" for d in self.directories if (d / f"{ibge}.parquet").exists()),
            None,
        )

    def points_in_bbox(
        self, ibge: str, south: float, west: float, north: float, east: float
    ) -> list[CadastrePoint]:
        """Pontos do município dentro do retângulo."""
        path = self._path(ibge)
        if path is None:
            msg = f"sem cadastro BDGD do município {ibge} em {self.directories}"
            raise FileNotFoundError(msg)
        # Lê o arquivo inteiro para a memória antes: em pasta sincronizada (Google Drive,
        # OneDrive) a leitura por trechos do pyarrow pega dados inválidos em arquivo recém-
        # gravado ("Couldn't deserialize thrift"). Cada cadastro tem poucos MB.
        t = pq.read_table(
            pa.BufferReader(path.read_bytes()),
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
