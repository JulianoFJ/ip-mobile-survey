# Como contribuir

1. Toda mudança nasce de uma issue. Branch a partir de `main` atualizada: `feat/<nº>-descricao`, `fix/…`, `exp/…` (ver §16.3 da especificação).
2. Commits em [Conventional Commits](https://www.conventionalcommits.org) (`feat:`, `fix:`, `docs:`…). O hook de pre-commit valida.
3. Antes de abrir o PR: `make check`.
4. PR pequeno (≤ 400 linhas), com o template preenchido, entra por **squash merge**.
5. Algoritmo novo exige: código em `domain/extraction/`, teste, entrada no benchmark e página em `docs/algorithms/`.
6. Mudança de arquitetura exige ADR em `docs/adr/`.
