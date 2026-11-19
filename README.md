# ip-mobile-survey

Plataforma de levantamento móvel de ativos de iluminação pública (Houer Consultoria e Concessões).
Recebe capturas 360° + GNSS/RTK (+ LiDAR), processa em nuvem e entrega atributos por poste e por vão,
com nível de confiança declarado.

A **fonte de verdade técnica** é [`docs/especificacao.md`](docs/especificacao.md).

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) ≥ 0.5 (instala o Python 3.12 automaticamente)
- Docker + Docker Compose
- GNU Make

## Início rápido

```bash
make install   # dependências + hooks de pre-commit + .env
make check     # lint, tipos, arquitetura e testes
make up        # PostGIS, MinIO e Prefect locais
make api       # API em http://localhost:8000/docs
```

| Serviço | Endereço |
|---|---|
| API (OpenAPI) | http://localhost:8000/docs |
| MinIO (console) | http://localhost:9001 (minioadmin / minioadmin) |
| Prefect | http://localhost:4200 |
| PostGIS | localhost:5432 (ipsurvey / ipsurvey) |

`make help` lista todos os comandos.

## Estrutura

```
src/ipsurvey/
  domain/        entidades e algoritmos puros (sem I/O)
  application/   casos de uso e portas (interfaces)
  adapters/      implementações: fontes, storage, PostGIS, COLMAP, detector
  flows/         orquestração Prefect
  api/  cli/     entradas HTTP e linha de comando
  bootstrap.py   composição de dependências (único lugar)
```

As regras de dependência entre camadas são verificadas por `make arch` (import-linter).

## Status

Sprint 0 (Fundação). Ver o roadmap em §18 da especificação.
