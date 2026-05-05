FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
COPY apps/node_agent ./apps/node_agent
COPY packages/shared ./packages/shared
RUN pip install --no-cache-dir uv && uv sync --package gamehost-node-agent --no-dev

EXPOSE 8010
CMD [".venv/bin/uvicorn", "gamehost_node.main:app", "--host", "0.0.0.0", "--port", "8010"]
