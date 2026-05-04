FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY apps/api ./apps/api
COPY packages/shared ./packages/shared
RUN pip install --no-cache-dir uv && uv sync --package gamehost-api --no-dev

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "gamehost_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
