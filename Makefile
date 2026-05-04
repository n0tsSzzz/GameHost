UV := uv
NPM := npm
WEB_DIR := apps/web

.PHONY: install lint format typecheck test up down migrate revision seed web-lint web-build

install:
	$(UV) sync --all-packages --all-groups
	cd $(WEB_DIR) && $(NPM) install

lint:
	$(UV) run ruff check .
	cd $(WEB_DIR) && $(NPM) run lint

format:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .
	cd $(WEB_DIR) && $(NPM) run format

typecheck:
	$(UV) run mypy apps/api/src apps/worker/src apps/node_agent/src packages/shared/src
	cd $(WEB_DIR) && $(NPM) run typecheck

test:
	$(UV) run pytest

up:
	docker compose -f deploy/docker-compose.yml up -d

down:
	docker compose -f deploy/docker-compose.yml down

migrate:
	$(UV) run alembic -c apps/api/alembic.ini upgrade head

revision:
	$(UV) run alembic -c apps/api/alembic.ini revision --autogenerate

seed:
	$(UV) run python apps/api/scripts/seed_templates.py

web-lint:
	cd $(WEB_DIR) && $(NPM) run lint

web-build:
	cd $(WEB_DIR) && $(NPM) run build
