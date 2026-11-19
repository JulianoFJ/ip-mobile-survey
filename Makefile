.DEFAULT_GOAL := help
COMPOSE := docker compose -f infra/docker-compose.yml --env-file .env

help: ## Lista os comandos
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

.env:
	cp .env.example .env

install: .env ## Instala dependências e hooks de pre-commit
	uv sync --all-groups
	uv run pre-commit install --install-hooks -t pre-commit -t commit-msg

lint: ## ruff (lint + formato)
	uv run ruff check .
	uv run ruff format --check .

fmt: ## Formata o código
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## mypy estrito em domain e application
	uv run mypy src/ipsurvey/domain src/ipsurvey/application

arch: ## Verifica contratos de arquitetura (import-linter)
	uv run lint-imports --config importlinter.ini

test: ## Testes unitários e de propriedade
	uv run pytest tests/unit tests/property -q --cov --cov-report=term

test-integration: ## Testes de integração (requer Docker)
	uv run pytest tests/integration -q

check: lint typecheck arch test ## Tudo que o CI de PR exige

up: .env ## Sobe PostGIS, MinIO e Prefect
	$(COMPOSE) up -d
	@echo "PostGIS: localhost:5432 | MinIO: http://localhost:9001 | Prefect: http://localhost:4200"

down: ## Derruba os serviços locais
	$(COMPOSE) down

logs: ## Logs dos serviços
	$(COMPOSE) logs -f

api: ## Roda a API local com reload
	uv run uvicorn ipsurvey.api.main:app --reload

docs: ## Serve a documentação localmente
	uv run --group docs mkdocs serve

.PHONY: help install lint fmt typecheck arch test test-integration check up down logs api docs
