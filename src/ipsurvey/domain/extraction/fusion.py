"""Fusão das fontes por campo da planilha de simulação: imagem 360°, cadastro e mapa.

Cada fonte mede bem coisas diferentes, e a regra é escolher, campo a campo, a fonte que
mede melhor aquele campo. Todos os candidatos ficam guardados para a revisão ver quando as
fontes divergem.

| Campo | Preferida | Alternativa |
|---|---|---|
| AF distância entre postes | cadastro (≥ `MIN_SAMPLES` espaçamentos na rua) | imagem |
| AD posteação | cadastro (≥ 3 postes na rua) | imagem |
| AH lâmpadas por ponto | cadastro (pontos no mesmo poste) | imagem |
| R faixas de rodagem | mapa (tag `lanes`) | — |
| AG/AL altura, AJ braço | imagem (só ela mede) | — |
| larguras S–Y, AI | pendente: satélite e segmentação | — |
"""

from dataclasses import dataclass, field

from ipsurvey.domain.cadastre import RoadWay
from ipsurvey.domain.extraction.road import RoadEstimate
from ipsurvey.domain.extraction.street import StreetEstimate

MIN_SAMPLES = 3

IMAGEM = "imagem"
CADASTRO = "cadastro"
MAPA = "mapa"


@dataclass(frozen=True, slots=True)
class Candidate:
    """Valor proposto por uma fonte."""

    source: str
    value: float | int | str
    detail: str


@dataclass(frozen=True, slots=True)
class FusedField:
    """Campo da planilha com o valor escolhido e os candidatos de todas as fontes."""

    column: str
    label: str
    unit: str
    value: float | int | str | None
    source: str | None
    method: str
    candidates: tuple[Candidate, ...] = field(default=())

    @property
    def divergent(self) -> bool:
        """Duas fontes numéricas discordam em mais de 25%, ou textuais diferem."""
        vals = [c.value for c in self.candidates]
        if len(vals) < 2:
            return False
        if all(isinstance(v, int | float) for v in vals):
            nums = [float(v) for v in vals]
            lo, hi = min(nums), max(nums)
            return hi > 0 and (hi - lo) / hi > 0.25
        return len({str(v) for v in vals}) > 1


def _pick(
    column: str, label: str, unit: str, candidates: list[Candidate], pending: str
) -> FusedField:
    if not candidates:
        return FusedField(column, label, unit, None, None, pending)
    best = candidates[0]
    return FusedField(column, label, unit, best.value, best.source, best.detail, tuple(candidates))


def fuse(
    image: RoadEstimate,
    street: StreetEstimate | None,
    way: RoadWay | None,
) -> list[FusedField]:
    """Campos de levantamento (colunas R–AM) fundidos, na ordem da planilha.

    `candidates` vem na ordem de preferência; o primeiro é o escolhido.
    """
    seg = "Segmentação da superfície e medida no satélite — próxima etapa"
    out: list[FusedField] = []

    lanes: list[Candidate] = []
    if way is not None and way.lanes:
        lanes.append(
            Candidate(MAPA, way.lanes, f"OSM: lanes={way.lanes} ({way.name or way.highway})")
        )
    out.append(
        _pick(
            "R",
            "Faixas de rodagem",
            "",
            lanes,
            "Sem a tag lanes no OSM; contagem na imagem — próxima etapa",
        )
    )

    for col, label in (
        ("S", "Largura do passeio 1"),
        ("T", "Largura da via 1"),
        ("U", "Passeio central 1"),
        ("V", "Passeio central 2"),
        ("W", "Largura da via 2"),
        ("X", "Largura do passeio 2"),
        ("Y", "Canteiro central"),
        ("Z", "Ciclovia 1"),
        ("AA", "Ciclovia 2"),
        ("AB", "Estacionamento 1"),
        ("AC", "Estacionamento 2"),
    ):
        out.append(FusedField(col, label, "m", None, None, seg))

    arr: list[Candidate] = []
    if street is not None and street.arrangement and len(street.poles) >= 3:
        arr.append(
            Candidate(
                CADASTRO, street.arrangement, f"{len(street.poles)} postes da BDGD ao longo da via"
            )
        )
    if image.arrangement:
        arr.append(Candidate(IMAGEM, image.arrangement, f"{len(image.poles)} postes no panorama"))
    out.append(_pick("AD", "Posteação", "", arr, "Nenhum poste localizado"))

    out.append(
        FusedField(
            "AE",
            "Tipo de estrutura",
            "",
            None,
            None,
            "Classificação visual do poste — próxima etapa",
        )
    )

    vao: list[Candidate] = []
    if (
        street is not None
        and street.spacing_m is not None
        and street.spacing_samples >= MIN_SAMPLES
    ):
        vao.append(
            Candidate(
                CADASTRO,
                round(street.spacing_m, 1),
                f"Mediana de {street.spacing_samples} vãos da BDGD na via",
            )
        )
    if image.pole_spacing_m is not None:
        vao.append(
            Candidate(
                IMAGEM,
                round(image.pole_spacing_m, 1),
                f"Mediana de {image.spacing_samples} vão(s) no panorama",
            )
        )
    out.append(_pick("AF", "Distância entre postes", "m", vao, "Sem postes vizinhos suficientes"))

    lum = [lf for lf in image.luminaires]
    lum_det = f"{len(lum)} luminária(s) associada(s) a poste no panorama"
    alt = (
        [Candidate(IMAGEM, round(image.mounting_height_m, 1), lum_det)]
        if image.mounting_height_m
        else []
    )
    out.append(_pick("AG", "Altura da luminária", "m", alt, "Nenhuma luminária associada a poste"))

    qtd: list[Candidate] = []
    if street is not None and street.luminaires_per_pole:
        qtd.append(
            Candidate(CADASTRO, street.luminaires_per_pole, "Mediana de pontos por poste na BDGD")
        )
    if lum:
        por: dict[int, int] = {}
        for lf in lum:
            por[lf.pole_index] = por.get(lf.pole_index, 0) + 1
        qtd.append(Candidate(IMAGEM, sorted(por.values())[len(por) // 2], lum_det))
    out.append(_pick("AH", "Lâmpadas por ponto", "", qtd, "Sem cadastro e sem luminária associada"))

    out.append(
        FusedField(
            "AI", "Distância do poste à via", "m", None, None, "Posição do meio-fio — próxima etapa"
        )
    )
    braco = (
        [Candidate(IMAGEM, round(image.arm_projection_m, 1), lum_det)]
        if image.arm_projection_m is not None
        else []
    )
    out.append(_pick("AJ", "Projeção do braço", "m", braco, "Nenhuma luminária associada a poste"))
    out.append(_pick("AL", "Altura de instalação", "m", alt, "Nenhuma luminária associada a poste"))
    out.append(
        FusedField(
            "AM", "Projeção vertical", "m", None, None, "Inclinação do braço — próxima etapa"
        )
    )
    return out
