FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY apps/node_agent ./apps/node_agent
RUN pip install --no-cache-dir uv && uv sync --package gamehost-node-agent --no-dev

EXPOSE 8010
CMD ["uv", "run", "uvicorn", "gamehost_node.main:app", "--host", "0.0.0.0", "--port", "8010"]
