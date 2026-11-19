# Planilha de inspeção

Produto final do ipsurvey ([ADR 0006](../adr/0006-escopo-inspecao-unica.md)): uma linha por
**ponto de IP**, nas colunas **B–AW** da aba *Simulações* das planilhas de simulação, com as mesmas
letras e cabeçalhos. Assim, as colunas copiam e colam sem ajuste.

## Origem das colunas

| Origem | Colunas | Cor do cabeçalho |
|---|---|---|
| Levantamento móvel | Etiqueta, lat/long, faixas, larguras, posteação, estrutura, vão, alturas, projeções, nº de lâmpadas, 2º nível | Azul |
| Cadastro do município | Id cadastro, logradouro, tipo de lâmpada, potências, reator | Verde |
| Escritório | Simular, Padrão, classificações (viária, ciclovia, pedonal), Exclusivo, informações adicionais | Laranja |
| Fórmula da planilha | Q (POT TOTAL MALHA), AK (Pendor), AO e AV (pontos inspecionados) | Cinza, não preenchidas |

Células medidas com confiança abaixo de 0,7 ficam **amarelas** e devem ser revisadas antes da
simulação. A aba *Origem* mostra a origem e a confiança de cada célula.

## Como gerar

```bash
uv run ipsurvey exportar-planilha pontos.json inspecao.xlsx
```

`pontos.json` é uma lista de `InspectionPoint` (ver `ipsurvey.domain.inspection`). No pipeline, a
etapa P11 gera esses pontos a partir das observações.

## Contrato

`ipsurvey.domain.inspection.columns.COLUMNS`. O teste `test_columns_match_simulation_sheet`
compara com `tests/fixtures/simulacoes_cabecalho_B_AW.json`, copiado de
`Plataforma_IP/app/simulacao_nbr/modelo_planilha_simulacao.json`. Se a planilha de simulação mudar,
atualize os dois juntos.
