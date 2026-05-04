# Architecture

GameHost is a monorepo with four deployable units: public API, worker, node-agent, and web.

The API owns user-facing REST contracts and database state. The worker executes long-running lifecycle tasks. The node-agent is a thin authenticated Docker facade installed on game nodes. The web app uses the public API only.

## Decisions

| Decision | Choice |
| --- | --- |
| Backend language | Python 3.12+ |
| API framework | FastAPI |
| Persistence | PostgreSQL via async SQLAlchemy |
| Queue | ARQ on Redis |
| Node control | Docker SDK inside node-agent |

## C4 Context

```mermaid
C4Context
  title GameHost context
  Person(player, "Player")
  Person(admin, "Admin")
  System(gamehost, "GameHost", "Game server provisioning platform")
  System_Ext(minio, "MinIO", "Backup object storage")
  Rel(player, gamehost, "Creates and manages game servers")
  Rel(admin, gamehost, "Manages nodes, templates, audit")
  Rel(gamehost, minio, "Stores backups")
```

## C4 Container

```mermaid
C4Container
  title GameHost containers
  Person(user, "User")
  Container(web, "web", "Next.js", "Console UI")
  Container(api, "api", "FastAPI", "REST API and auth")
  Container(worker, "worker", "ARQ", "Lifecycle and backup jobs")
  Container(agent, "node-agent", "FastAPI + Docker SDK", "Controls containers on game nodes")
  ContainerDb(db, "PostgreSQL", "Relational state")
  Container(redis, "Redis", "Queue, cache and logs pub/sub")
  Rel(user, web, "Uses")
  Rel(web, api, "HTTPS JSON/SSE")
  Rel(api, db, "Async SQL")
  Rel(api, redis, "Tasks and logs")
  Rel(worker, redis, "Consumes jobs")
  Rel(worker, agent, "Bearer-auth HTTP")
  Rel(agent, redis, "Publishes logs")
```
