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

import statistics
from dataclasses import dataclass, field

from ipsurvey.domain.cadastre import RoadWay
from ipsurvey.domain.extraction.cross_section import CrossSection
from ipsurvey.domain.extraction.road import RoadEstimate, Side
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


#: Largura de faixa usada para estimar o número de faixas pela largura da pista.
LANE_WIDTH_M = 3.3
#: Anisotropia do eixo da pista abaixo da qual a medida provavelmente caiu num cruzamento.
MIN_AXIS_ANISOTROPY = 2.0


def pole_setback(
    image: RoadEstimate, section: CrossSection, *, max_along_m: float = 15.0
) -> list[float]:
    """Distâncias poste–meio-fio: postes perto da câmera menos o meio-fio do mesmo lado."""
    out: list[float] = []
    for p in image.poles:
        if abs(p.y_m) > max_along_m:
            continue
        curb = (
            section.curb_right_m
            if p.side is Side.RIGHT
            else section.curb_left_m
            if p.side is Side.LEFT
            else None
        )
        if curb is None:
            continue
        d = abs(p.x_m) - curb
        if -0.5 <= d <= 6.0:
            out.append(max(d, 0.0))
    return out


def fuse(  # noqa: PLR0915 (uma regra por campo, em sequência, de propósito)
    image: RoadEstimate,
    street: StreetEstimate | None,
    way: RoadWay | None,
    section: CrossSection | None = None,
    axis_anisotropy: float | None = None,
) -> list[FusedField]:
    """Campos de levantamento (colunas R–AM) fundidos, na ordem da planilha.

    `candidates` vem na ordem de preferência; o primeiro é o escolhido.
    """
    seg = "Corte transversal sem fatias suficientes (pista fora do quadro, cruzamento ou oclusão)"
    out: list[FusedField] = []
    cruz = axis_anisotropy is not None and axis_anisotropy < MIN_AXIS_ANISOTROPY
    obs = " Provável cruzamento: conferir." if cruz else ""
    sec_det = (
        f"Corte transversal do chão segmentado "
        f"({section.rows_used}/{section.rows_total} fatias).{obs}"
        if section
        else ""
    )

    def largura(valor: float | None) -> list[Candidate]:
        return (
            [Candidate(IMAGEM, round(valor, 1), sec_det)] if section and valor is not None else []
        )

    lanes: list[Candidate] = []
    if way is not None and way.lanes:
        lanes.append(
            Candidate(MAPA, way.lanes, f"OSM: lanes={way.lanes} ({way.name or way.highway})")
        )
    if section and section.road_width_m and not cruz:
        n = max(1, round(section.road_width_m / LANE_WIDTH_M))
        lanes.append(
            Candidate(IMAGEM, n, f"Largura da pista ÷ {LANE_WIDTH_M} m (estimativa grosseira)")
        )
    out.append(
        _pick("R", "Faixas de rodagem", "", lanes, "Sem a tag lanes no OSM e sem largura da pista")
    )

    out.append(
        _pick(
            "S",
            "Largura do passeio 1",
            "m",
            largura(section.sidewalk_left_m if section else None),
            seg,
        )
    )
    out.append(
        _pick("T", "Largura da via 1", "m", largura(section.road_width_m if section else None), seg)
    )
    out.append(
        FusedField(
            "U", "Passeio central 1", "m", None, None, "Não separado do canteiro nesta versão"
        )
    )
    out.append(
        FusedField(
            "V", "Passeio central 2", "m", None, None, "Não separado do canteiro nesta versão"
        )
    )
    out.append(
        _pick(
            "W",
            "Largura da via 2",
            "m",
            largura(section.road2_width_m if section else None),
            "Sem segunda pista além de canteiro",
        )
    )
    out.append(
        _pick(
            "X",
            "Largura do passeio 2",
            "m",
            largura(section.sidewalk_right_m if section else None),
            seg,
        )
    )
    out.append(
        _pick(
            "Y",
            "Canteiro central",
            "m",
            largura(section.median_m if section else None),
            "Sem canteiro entre pistas no corte",
        )
    )
    for col, label in (
        ("Z", "Ciclovia 1"),
        ("AA", "Ciclovia 2"),
        ("AB", "Estacionamento 1"),
        ("AC", "Estacionamento 2"),
    ):
        out.append(
            FusedField(
                col, label, "m", None, None, "Classe não separada pelo segmentador — próxima etapa"
            )
        )

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

    recuos = pole_setback(image, section) if section else []
    ai = (
        [
            Candidate(
                IMAGEM,
                round(statistics.median(recuos), 1),
                f"{len(recuos)} poste(s) × meio-fio do mesmo lado.{obs}",
            )
        ]
        if recuos
        else []
    )
    out.append(
        _pick(
            "AI",
            "Distância do poste à via",
            "m",
            ai,
            "Sem poste perto com o meio-fio do lado medido",
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
