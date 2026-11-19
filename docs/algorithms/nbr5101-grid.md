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

## Testes

- Unitários: casos de referência do DIALux, ruído de ponto flutuante, entradas inválidas.
- Propriedade (hypothesis): D ≤ 3 m; N ≥ 10 e mínimo; 3 pontos por faixa; pontos estritamente
  dentro do vão; simetria; linha central de cada faixa no eixo da faixa.

## Limitações

- Malha retangular: vias curvas devem ser retificadas no eixo antes de usar.
- Passeio: calcular como área separada, com `lanes=1`.
- Pendente: confirmar no texto da NBR 5101:2024 se há diferença em relação à EN 13201-3 (por
  exemplo, no número de pontos transversais para faixas largas).
