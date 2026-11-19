# 0001: Monorepo Python com uv

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto
Equipe pequena, domínio geoespacial/visão computacional, necessidade de reprodutibilidade total (§2).

## Decisão
Um único repositório com o pacote `ipsurvey` em `src/`, gerenciado por **uv** com `uv.lock` versionado. Python 3.12.

## Alternativas consideradas
- Poetry: mais lento, sem workspaces nativos.
- Multi-repo / microserviços: cerimônia sem ganho no MVP (§2, princípio 10).

## Consequências
Builds reprodutíveis via lockfile; um só CI. Separar serviços só quando houver medição que justifique.
