# Fusão de fontes: imagem 360°, cadastro e mapa

Cada campo de levantamento da planilha de simulação (colunas R a AM) é preenchido pela fonte que mede melhor aquele campo. Os valores das outras fontes ficam guardados como candidatos (`domain/extraction/fusion.py`).

| Campo | Preferida | Alternativa | Por quê |
|---|---|---|---|
| AF distância entre postes | cadastro (≥ 3 vãos na rua) | imagem | Dezenas de postes ao longo do eixo, contra dois ou três por foto |
| AD posteação | cadastro (≥ 3 postes na rua) | imagem | A PIP da BDGD só tem postes **com IP**; a câmera vê também os postes sem luminária |
| AH lâmpadas por ponto | cadastro | imagem | Pontos da PIP na mesma coordenada do PONNOT |
| R faixas | mapa (tag `lanes`) | — | Contagem na imagem: próxima etapa |
| AG/AL altura, AJ braço | imagem | — | Só a imagem mede |
| S–Y larguras, AI | pendente | — | O OSM não tem largura (0% no golden); o caminho é o satélite e a segmentação |

## Como a rua é montada

1. **Mapa:** vias do OSM a até 200 m da captura (`adapters/maps/overpass.py`, com cache em `data/osm/`). A via da captura é o eixo mais próximo, a até 25 m, sem contar vias de serviço.
2. **Cadastro:** pontos da BDGD no mesmo retângulo, lidos dos parquets que o Ignis publica (`adapters/cadastre/bdgd.py`). Pontos na mesma coordenada viram um poste (`group_poles`).
3. **Referência linear:** cada poste vai para a via de eixo mais próximo, a até 20 m (`assign_poles`). A posição ao longo do eixo dá os vãos de cada lado (`street_estimate`), entre 8 e 70 m, e o lado dá a posteação.

## O que foi medido no golden `panoramax-br-v0`

- Cadastro BDGD disponível em 38 das 68 capturas (as 9 cidades de MG publicadas pelo Ignis).
- **AF:** de 6 capturas (só imagem) para 31. Em 27 delas o valor vem do cadastro, com mediana de **32,1 m** (de 23 a 45 m).
- **R:** 36 de 68 pelo OSM. **AH:** 58 de 68. **Logradouro:** 61 de 68.
- **Posteação:** imagem e cadastro divergem em 21 capturas, o que é esperado pela diferença entre "todo poste" e "poste com IP".

## Casamento poste a poste: ainda não

O `match_nearest` existe e está testado, mas a interface não o usa. No golden, casar cada poste detectado na foto com um poste da BDGD **não supera o acaso**. Varrendo o rumo de −180° a +180°, nenhum giro casa mais que o ruído: pico de 13 contra média de 7,2 casamentos a até 4 m, e só 4 com o rumo original.

Os erros somados passam do espaçamento entre postes:

- GPS da câmera: alguns metros;
- distância estimada num quadro só;
- coordenada esquemática do PONNOT: o Ignis mediu mediana de 6,3 m até o eixo da via.

O casamento volta com triangulação entre quadros consecutivos e GNSS RTK. A fusão **por rua** não depende dele, porque usa estatística de muitos vãos.
