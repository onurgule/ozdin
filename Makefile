.PHONY: up down migrate seed test lint fmt api-dev flutter-analyze smoke

COMPOSE := docker compose -f infra/docker/docker-compose.yml

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

migrate:
	cd apps/api && .venv/bin/alembic upgrade head 2>/dev/null || (python -m alembic upgrade head)

seed:
	cd apps/api && python -m scripts.seed_sample || true
	cd packages/source_ingestion_tools && pip install -e ../../apps/api -e . -q && python -m source_ingestion_tools ingest --format qa --path ../../docs/sample_data/sample_qa.jsonl
	cd packages/source_ingestion_tools && python -m source_ingestion_tools ingest --format quran --path ../../docs/sample_data/sample_quran.jsonl

test:
	cd apps/api && pytest tests -v --tb=short

lint:
	cd apps/api && ruff check . && mypy yasar_nuri_api
	cd apps/mobile_web_flutter && dart analyze

fmt:
	cd apps/api && ruff format .
	cd apps/mobile_web_flutter && dart format lib test

api-dev:
	cd apps/api && uvicorn yasar_nuri_api.main:app --reload --host 0.0.0.0 --port 8000

flutter-analyze:
	cd apps/mobile_web_flutter && dart analyze

smoke:
	python scripts/smoke_api.py
