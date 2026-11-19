# 0003: Arquitetura hexagonal com import-linter

- **Status:** aceita
- **Data:** 2026-11-19

## Contexto
Algoritmos precisam ser testáveis sem S3, banco ou fila, e trocáveis por versão (§2, princípio 5).

## Decisão
Camadas `domain → application (portas) → adapters → bootstrap → api|cli|flows`, verificadas por **import-linter** (`importlinter.ini`) no CI.

## Alternativas consideradas
Convenção sem verificação automática: degrada com o tempo.

## Consequências
Composição só em `bootstrap.py`. Violação de camada quebra o job `architecture`.
