# GameHost

GameHost is a Python-first MVP platform for provisioning and managing multiplayer game servers.

## Local Development

```bash
make install
make up
make lint
make typecheck
make test
```

Copy `.env.example` to `.env` for local overrides. All routine actions are exposed through `make` targets or `uv run`.

## Workspace

- `apps/api` - public FastAPI REST API.
- `apps/worker` - ARQ worker for lifecycle jobs.
- `apps/node_agent` - FastAPI service that controls Docker on each node.
- `apps/web` - Next.js frontend.
- `packages/shared` - shared Python enums and contracts.
