# 0002: Prefect como orquestrador

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto
Pipeline em lote, por segmento, com retries, cache por conteúdo e pools CPU/GPU (§7).

## Decisão
**Prefect 3**, com chave de cache derivada de hashes de entrada + parâmetros + versão.

## Alternativas consideradas
- Airflow: pesado para lote dinâmico por segmento.
- Dagster: bom, mas curva maior; Prefect atende com menos cerimônia.

## Consequências
Flows ficam em `ipsurvey.flows` e só chamam casos de uso; o domínio não conhece o Prefect.
