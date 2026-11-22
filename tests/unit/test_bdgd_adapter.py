from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from ipsurvey.adapters.cadastre.bdgd import BdgdParquetCadastre


def _grava(pasta: Path, ibge: str, lat: float) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    t = pa.table(
        {
            "id_ponto": ["1", "2"],
            "latitude": pa.array([lat, lat + 1], pa.float32()),
            "longitude": pa.array([-44.0, -44.0], pa.float32()),
            "tecnologia": ["LED", "VS"],
            "potencia_lampada_w": pa.array([100.0, 150.0], pa.float32()),
            "area_urbana": [True, False],
        }
    )
    pq.write_table(t, pasta / f"{ibge}.parquet")


def test_varias_pastas_em_ordem(tmp_path: Path) -> None:
    pub, loc = tmp_path / "publicados", tmp_path / "locais"
    _grava(pub, "3106200", -19.9)
    _grava(loc, "5300108", -15.8)
    _grava(loc, "3106200", -10.0)  # a publicada tem preferência
    cad = BdgdParquetCadastre(f"{pub}:{loc}")
    assert cad.available() == {"3106200", "5300108"}
    pts = cad.points_in_bbox("3106200", -20.5, -45, -19.5, -43)
    assert [p.point_id for p in pts] == ["1"]
    assert pts[0].technology == "LED"
    assert len(cad.points_in_bbox("5300108", -16, -45, -15, -43)) == 1


def test_municipio_sem_cadastro(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        BdgdParquetCadastre(tmp_path).points_in_bbox("1234567", 0, 0, 1, 1)
