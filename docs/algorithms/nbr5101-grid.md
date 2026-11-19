# Malha de cálculo NBR 5101

**Código:** `ipsurvey.domain.nbr5101.grid` · **Versão:** `nbr5101_grid_v2` · **Norma:** ABNT NBR 5101:2024, seção 5.1

> Uso: módulo fotométrico (fora do MVP estrutural). Fica no domínio porque é compartilhado.

## Regras

| Área | Eixo | Regra | Seção |
|---|---|---|---|
| Pista e calçada | Longitudinal | D = S/N ≤ 3 m. S ≤ 30 m → N = 10; S > 30 m → menor N inteiro com D ≤ 3 m. Primeiro ponto a D/2 do poste | 5.1.1.1 / 5.1.2.2 |
| Pista | Transversal | Sempre 3 pontos por faixa, d = L/3; ponto central no eixo da faixa; extremos a d/2 do meio-fio | 5.1.1.2 |
| Calçada | Transversal | Largura ≤ 4,5 m → 3 pontos; > 4,5 m → menor inteiro com d ≤ 1,5 m; extremos a d/2 das bordas | 5.1.2.1 |

Funções: `calculation_grid(S, W, lanes)` para a pista e `sidewalk_grid(S, largura)` para a calçada.

## Origem e validação

- Regras conferidas no texto da NBR 5101:2024 em 19/11/2026. Exemplar licenciado no Drive da Houer.
- A malha da pista é igual à de `malha_en13201` da Plataforma_IP, validada contra 33 grades de 10
  relatórios DIALux (Cajamar, 2026). Os dois módulos precisam usar a **mesma** malha: Uo é
  Emin/Emed, e o mínimo depende de onde se amostra.
- A v1 tratava a calçada como uma faixa (sempre 3 pontos). Isso estava errado para calçadas com
  mais de 4,5 m e foi corrigido na v2.

## Testes

- Unitários: limiares da norma (S = 30 m; largura da calçada = 4,5 m), casos do DIALux, ruído de
  ponto flutuante, entradas inválidas.
- Propriedade (hypothesis): D ≤ 3 m; N ≥ 10 e mínimo; 3 pontos por faixa; d ≤ 1,5 m e c mínimo na
  calçada; pontos dentro da área; simetria; linha central de cada faixa no eixo.

## Limitações

- Malha retangular: vias curvas devem ser retificadas no eixo antes de usar.
- Praças e áreas abertas (5.2) e malha de luminância/iluminância vertical (5.4, 5.5) ainda não
  implementadas.
