FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
COPY apps/node_agent ./apps/node_agent
COPY packages/shared ./packages/shared
RUN pip install --no-cache-dir uv && uv sync --package gamehost-worker --no-dev

CMD [".venv/bin/arq", "gamehost_worker.main.WorkerSettings"]
