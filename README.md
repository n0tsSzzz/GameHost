# GameHost

GameHost is a Python-first platform for provisioning and managing multiplayer game servers from a web console. The MVP covers authentication, game templates, node administration, server lifecycle tasks, member roles, log streaming, backups, audit, metrics, and deployment scaffolding.

The product goal is simple: a user chooses a game template, creates a server, and the platform schedules work to a worker that provisions a Docker container on a registered game node through a thin node-agent.

## What It Does

- User auth with access JWT and httpOnly refresh cookie.
- Admin-managed game templates and game nodes.
- Server lifecycle API: create, start, stop, restart, delete.
- Background task mirror for UI-visible long-running operations.
- Node-agent API for Docker container operations.
- Server member roles: `viewer` and `operator`.
- Real-time log plumbing through Redis pub/sub and SSE.
- Backup and restore task records.
- Audit log API for admins.
- Prometheus metrics and Grafana provisioning.
- Next.js operations console with server, detail, and admin views.

## Tech Stack

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 async + asyncpg
- Alembic migrations
- Pydantic v2 + pydantic-settings
- ARQ worker on Redis
- Redis for queue/log pub-sub
- Docker SDK for node-agent container control
- httpx for internal async HTTP
- python-jose + argon2-cffi for JWT/password hashing
- structlog-ready JSON logging foundation
- prometheus-fastapi-instrumentator + prometheus-client

### Frontend

- Next.js 15 App Router
- TypeScript
- Tailwind CSS
- shadcn-style local UI primitives
- TanStack Query
- lucide-react icons
- next-themes

### Infrastructure

- Docker and Docker Compose
- PostgreSQL
- Redis
- MinIO
- Prometheus, Grafana, Loki, Promtail
- GitHub Actions CI and GHCR image publishing
- Ansible role for node-agent provisioning
- uv workspace for Python packages
- Ruff, mypy strict, pytest, pre-commit, Make

## Architecture

GameHost is a monorepo with four deployable units:

```text
browser
  |
  v
web (Next.js)
  |
  v
api (FastAPI) ---> PostgreSQL
  |                    ^
  v                    |
Redis / ARQ -------- worker
                       |
                       v
                 node-agent (FastAPI)
                       |
                       v
                 Docker game containers
```

The API owns public REST contracts, auth, RBAC, and database state. It does not call Docker directly. Long-running operations create `tasks` rows and are executed by the worker. The worker chooses nodes and calls node-agent over Bearer-auth HTTP. Node-agent is intentionally thin: it has no main database access and only wraps Docker operations on a game node.

Cross-cutting services:

- PostgreSQL stores users, refresh tokens, templates, nodes, servers, members, backups, tasks, and audit.
- Redis backs ARQ and log streaming.
- MinIO is the object-storage target for backups.
- Prometheus/Grafana/Loki/Promtail provide observability.

More detail is in [docs/architecture.md](docs/architecture.md).

## Repository Layout

```text
.
├── apps/
│   ├── api/          # public FastAPI API
│   ├── worker/       # ARQ worker
│   ├── node_agent/   # FastAPI Docker facade installed on game nodes
│   └── web/          # Next.js console
├── packages/
│   └── shared/       # shared Python enums and DTO helpers
├── deploy/
│   ├── ansible/
│   ├── prometheus/
│   ├── grafana/
│   ├── loki/
│   └── promtail/
├── docs/
│   ├── architecture.md
│   └── runbook.md
├── .github/workflows/
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── uv.lock
```

## Local Development

Install dependencies:

```bash
make install
```

Create local environment config:

```bash
cp .env.example .env
```

Start the whole local stack:

```bash
make up
```

The compose stack starts PostgreSQL, Redis, MinIO, API, worker, node-agent, web,
and observability services. Migrations and default seed data run as one-shot
compose services before the app starts.

Run checks:

```bash
make lint
make typecheck
make test
```

The web app is available at:

```text
http://localhost:3000
```

The API is available directly at `http://localhost:8000/api/v1`. The web
container also proxies `/api/*` to the API service internally.

API health endpoints:

```text
GET /api/v1/healthz
GET /api/v1/readyz
GET /metrics
```

## Common Commands

```bash
make install      # sync Python workspace and install web dependencies
make lint         # Ruff + ESLint
make format       # Ruff format/fix + Prettier
make typecheck    # mypy strict + tsc
make test         # pytest
make up           # start local compose stack
make down         # stop local compose stack
make migrate      # run Alembic migrations
make revision     # create Alembic autogenerate revision
make seed         # seed default game templates
make web-build    # production Next.js build
```

## API Surface

Main API prefix: `/api/v1`.

- Auth: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`
- Templates: `/templates`
- Nodes: `/nodes`
- Servers: `/servers`
- Logs: `/servers/{server_id}/logs`, `/servers/{server_id}/logs/stream`
- Members: `/servers/{server_id}/members`, `/invites/{token}/accept`
- Backups: `/servers/{server_id}/backups`, `/backups/{backup_id}/restore`
- Tasks: `/tasks/{task_id}`
- Audit: `/audit`

Errors are returned as `application/problem+json` where handled by the API exception layer.

## Data Model

Core tables:

- `users`
- `refresh_tokens`
- `game_templates`
- `nodes`
- `servers`
- `server_members`
- `server_invites`
- `backups`
- `tasks`
- `audit_log`

IDs are UUID-based for user-facing entities. Timestamps are timezone-aware. JSON columns hold template defaults, resource hints, task payloads, audit metadata, and server environment overrides.

## Security Model

- Passwords use Argon2.
- Access tokens are JWTs.
- Refresh tokens are stored as hashes and delivered by httpOnly cookies.
- Admin endpoints use role guards.
- Server lifecycle and backup operations require owner/operator access.
- Node-agent uses Bearer API key authentication.
- Node-agent is isolated from the primary database.
- Secrets live in `.env` or deployment secret stores, never in source code.

## Observability

- FastAPI metrics are exposed at `/metrics`.
- Custom metric names include:
  - `gh_servers_total`
  - `gh_task_duration_seconds`
  - `gh_node_capacity_used_ratio`
  - `gh_arq_jobs_in_flight`
  - `gh_arq_jobs_failed_total`
- Grafana provisioning lives under `deploy/grafana/`.
- Prometheus config lives under `deploy/prometheus/`.
- Loki and Promtail configs live under `deploy/loki/` and `deploy/promtail/`.

## Deployment

Deployment-oriented scaffolding includes:

- one root `docker-compose.yml` for the local/full stack
- GHCR image build workflow on `v*` tags
- Ansible `node-agent` role with systemd unit

Operational instructions are in [docs/runbook.md](docs/runbook.md).

## Current MVP Status

The repository contains an implemented MVP skeleton across all planned stages. It is suitable for local development, API/domain testing, frontend iteration, and deployment hardening. Some production-grade behaviors are intentionally thin in this MVP, especially real MinIO streaming details, full UI mutation forms, and end-to-end game-container provisioning against real remote nodes.

The current verification baseline:

```bash
make lint
make typecheck
make test
make web-build
```
