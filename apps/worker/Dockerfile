FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY apps/worker ./apps/worker
COPY packages/shared ./packages/shared
RUN pip install --no-cache-dir uv && uv sync --package gamehost-worker --no-dev

CMD ["uv", "run", "arq", "gamehost_worker.main.WorkerSettings"]
