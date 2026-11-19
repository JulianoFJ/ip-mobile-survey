# Malha de cálculo NBR 5101

**Código:** `ipsurvey.domain.nbr5101.grid` · **Versão:** `nbr5101_grid_v1`

## Método

Para um vão S (m) de uma pista com largura W (m) e `k` faixas de rolamento:

| Direção | Nº de pontos | Espaçamento |
|---|---|---|
| Longitudinal (x, ao longo do vão) | N = máx(10, ⌈S/3⌉) | D = S/N ≤ 3 m |
| Transversal (y, na largura) | 3·k | W/(3·k) |

Os pontos ficam no **centro de cada célula**: x_i = (i + ½)·S/N e y_j = (j + ½)·W/(3k).
O ponto do meio de cada trinca transversal cai no eixo da faixa. É nessa linha que se calcula a
uniformidade longitudinal (Ul).

## Origem e validação

A regra é a mesma de `malha_en13201` na Plataforma_IP (`photometric_engine/motor.py`). Lá ela foi
conferida contra 33 grades de 10 relatórios DIALux (Cajamar, 2026): 3, 6 e 12 linhas para 1, 2 e 4
faixas, e 10 a 14 colunas para vãos de 19 a 40 m. Os dois módulos (estrutural e fotométrico)
precisam usar a **mesma** malha. O Uo é Emin/Emed, e o mínimo depende de onde se amostra: uma malha
mais densa encontra mínimos que a malha da norma não vê.

### Conferência com a NBR 5101 (19/11/2026)

O texto da NBR 5101:2024 não está disponível publicamente: é vendido pela ABNT e não há cópia no
acervo da Houer. A conferência usou as figuras do rascunho da revisão, apresentadas pela comissão
de estudo no Workshop Abilumi 2019 (Drive do Time de IP, `16. Eventos/…/Palestra 7-NBR5101`,
capítulo 6, "Malha de projeto e verificação"):

| Item | Rascunho NBR 5101 (Fig. 1 e 2) | Este módulo |
|---|---|---|
| Espaçamento longitudinal | D = S/N | ✔ igual |
| Espaçamento transversal | d = L/3 por faixa (3 pontos) | ✔ igual |
| Posição | D/2 e d/2 das bordas (centro da célula) | ✔ igual |
| Calçada | Malha própria, 3 pontos na largura | ✔ calcular com `lanes=1` |
| Regra de N (mín. 10, D ≤ 3 m) | Não aparece nas figuras | Vem da EN 13201-3 e da validação contra o DIALux |

**Ainda falta:** confirmar a regra de N no texto final de 2024. Quando a Houer tiver a norma,
conferir a seção de malha de cálculo e atualizar esta página.

## Testes

- Unitários: casos de referência do DIALux, ruído de ponto flutuante, entradas inválidas.
- Propriedade (hypothesis): D ≤ 3 m; N ≥ 10 e mínimo; 3 pontos por faixa; pontos estritamente
  dentro do vão; simetria; linha central de cada faixa no eixo da faixa.

## Limitações

- Malha retangular: vias curvas devem ser retificadas no eixo antes de usar.
- Passeio: calcular como área separada, com `lanes=1`.
- Regra de N ainda não conferida no texto final da NBR 5101:2024 (ver acima).
