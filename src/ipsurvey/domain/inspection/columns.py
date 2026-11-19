"""Contrato da planilha de inspeção: colunas B–AW da aba "Simulações" (ADR 0006).

Letras e cabeçalhos idênticos aos de `modelo_planilha_simulacao.json` da Plataforma_IP. É pela
letra que o motor de simulação lê a planilha, então a ordem e as letras não podem mudar.
"""

from dataclasses import dataclass
from enum import StrEnum


class Source(StrEnum):
    """De onde vem o valor de uma coluna."""

    SURVEY = "levantamento"  # medido pelo levantamento móvel
    CADASTRE = "cadastro"  # cadastro de IP do município
    OFFICE = "escritorio"  # classificação feita pelo analista
    SHEET = "planilha"  # fórmula da planilha de simulação: o ipsurvey não preenche


@dataclass(frozen=True)
class Column:
    """Uma coluna da planilha de inspeção.

    Attributes:
        letter: Letra da coluna na aba Simulações.
        header: Cabeçalho exato (com a grafia original).
        field: Nome do campo em `InspectionPoint`, ou None para colunas de fórmula.
        source: Origem padrão do valor.
    """

    letter: str
    header: str
    field: str | None
    source: Source


_S, _C, _O, _P = Source.SURVEY, Source.CADASTRE, Source.OFFICE, Source.SHEET

COLUMNS: tuple[Column, ...] = (
    Column("B", "Id cadastro", "cadastre_id", _C),
    Column("C", "Simular", "simulate", _O),
    Column("D", "Automatizada", "automated", _S),
    Column("E", "Etiqueta", "label", _S),
    Column("F", "Padrão", "pattern", _O),
    Column("G", "Logradouro", "street", _C),
    Column("H", "latitude", "latitude", _S),
    Column("I", "longitude", "longitude", _S),
    Column("J", "Classificação viária", "road_class", _O),
    Column("K", "Classificação ciclovia", "cycle_class", _O),
    Column("L", "Classificação pedonal", "pedestrian_class", _O),
    Column("M", "Tipo de lâmpada", "lamp_type", _C),
    Column("N", "Potencia da lâmpada", "lamp_power_w", _C),
    Column("O", "Reator", "ballast", _C),
    Column("P", "Potencia 2o nivel", "lamp_power_2nd_w", _C),
    Column("Q", "POT TOTAL MALHA", None, _P),
    Column("R", "Faixas de Rodagem", "lanes", _S),
    Column("S", "Largura Passeio 1", "sidewalk_1_m", _S),
    Column("T", "Largura Via 1", "road_1_m", _S),
    Column("U", "largura Passeio Central 1", "central_sidewalk_1_m", _S),
    Column("V", "largura Passeio Central 2", "central_sidewalk_2_m", _S),
    Column("W", "Largura Via 2", "road_2_m", _S),
    Column("X", "largura Passeio 2", "sidewalk_2_m", _S),
    Column("Y", "largura Canteiro Central", "median_m", _S),
    Column("Z", "largura Ciclovia 1", "cycleway_1_m", _S),
    Column("AA", "largura Ciclovia 2", "cycleway_2_m", _S),
    Column("AB", "estacionamento 1", "parking_1_m", _S),
    Column("AC", "estacionamento 2", "parking_2_m", _S),
    Column("AD", "posteacao", "arrangement", _S),
    Column("AE", "Tipo de estrutura", "structure_type", _S),
    Column("AF", "distancia entre postes", "pole_spacing_m", _S),
    Column("AG", "altura da luminaria", "luminaire_height_m", _S),
    Column("AH", "qtd de Lampadas IP Princ", "luminaires_main", _S),
    Column("AI", "distancia Poste a via", "pole_setback_m", _S),
    Column("AJ", "projecao do braço", "arm_projection_m", _S),
    Column("AK", "Pendor", None, _P),
    Column("AL", "Altura de Instalação", "mounting_height_m", _S),
    Column("AM", "Projeção Vertical", "vertical_projection_m", _S),
    Column("AN", "Exclusivo", "exclusive", _O),
    Column("AO", "Quantidade de pontos inspecionados IP Veic", None, _P),
    Column("AP", "qtd de Lampadas IP 2o nivel", "luminaires_2nd", _S),
    Column("AQ", "Tipo de posteação 2o nivel", "arrangement_2nd", _S),
    Column("AR", "Distanciamento 2o nivel", "spacing_2nd_m", _S),
    Column("AS", "Altura da luminaria 2o nivel", "luminaire_height_2nd_m", _S),
    Column("AT", "Projecao 2o nivel", "arm_projection_2nd_m", _S),
    Column("AU", "Distancia poste-via 2o nivel", "pole_setback_2nd_m", _S),
    Column("AV", "Quantidade de pontos inspecionados IP Sec", None, _P),
    Column("AW", "informacoes Adicionais", "notes", _O),
)

FIELD_COLUMNS: dict[str, Column] = {c.field: c for c in COLUMNS if c.field is not None}
