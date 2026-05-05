# Промпт для Claude Code: GameHost — платформа управления игровыми серверами

> Скопируй весь этот файл (или приложи как `PROMPT.md`) в качестве первого сообщения Claude Code в пустом репозитории. Промпт самодостаточен.

---

## 0. Роль и стиль работы

Ты — старший backend-инженер. Тебе нужно собрать **MVP** платформы по описанному ниже техническому заданию. Работай инкрементально: маленькими PR-подобными шагами с осмысленными коммитами; после каждого этапа запускай линтер, типы и тесты; не переходи к следующему этапу, пока предыдущий не зелёный.

**Нерушимые правила:**
1. Стек строго Python-first (см. §2). Никакого Go, никакой Java, никакого Node.js на бэкенде. Next.js — только во фронтенде.
2. Весь Python-код — `async/await` там, где есть I/O. Синхронный SQLAlchemy/requests запрещён.
3. Полная типизация, `mypy --strict` без ошибок.
4. Никаких секретов в коде — только `.env` через `pydantic-settings`. Пиши `.env.example`.
5. Никаких «магических» ручных шагов в README — всё через `make`-цели или `uv run`.
6. Если сомневаешься в архитектурном решении — задай уточняющий вопрос **до** написания кода, не после.

---

## 1. Что строим (контекст продукта)

**GameHost** — веб-сервис, который позволяет пользователю в пару кликов поднять игровой сервер для многопользовательской игры (Minecraft, Counter-Strike 2, Valheim, Terraria, Rust) без ручной настройки VPS, портов, конфигов и бэкапов.

**Сценарии:**
1. **Создание сервера.** Пользователь логинится, выбирает игру и шаблон, задаёт имя/параметры → платформа ставит задачу в очередь, разворачивает Docker-контейнер на свободной ноде, возвращает `host:port` для подключения.
2. **Управление.** Пользователь из панели стартует/стопает/рестартует инстанс, читает логи (стрим), правит env и конфиги, делает/восстанавливает бэкапы.
3. **Совместная игра.** Владелец приглашает друзей по email/ссылке и выдаёт им роль (`viewer`, `operator`).
4. **Администрирование.** Админ заводит ноды, публикует шаблоны игр, ставит лимиты, видит аудит, мониторит здоровье.
5. **Наблюдаемость.** Метрики и логи со всех инстансов и сервисов агрегируются в Prometheus/Loki, дашборды — в Grafana.

**Категории пользователей:**
- `user` — владелец серверов (создаёт, управляет, приглашает).
- `member` — приглашённый, действует в рамках выданной роли.
- `admin` — управляет нодами, шаблонами, видит весь аудит.

---

## 2. Технологический стек (фиксированный)

### Бэкенд
- **Python 3.12+**
- **FastAPI** — REST API, OpenAPI из коробки.
- **SQLAlchemy 2.0** (async, декларативные типизированные модели) + **asyncpg**.
- **Alembic** — миграции.
- **Pydantic v2** — DTO; **pydantic-settings** — конфиг.
- **ARQ** — асинхронная очередь задач на Redis (это идейный аналог Go-шного Asynq для Python — выбран сознательно).
- **Redis 7** — брокер ARQ + кэш + pub/sub для стрима логов.
- **Docker SDK for Python (`docker`)** — управление контейнерами на нодах.
- **httpx** (async) — внутренние HTTP-вызовы между сервисами.
- **python-jose[cryptography]** + **argon2-cffi** — JWT (access+refresh) и хеш паролей.
- **structlog** — структурированные JSON-логи.
- **prometheus-fastapi-instrumentator** + **prometheus-client** — метрики.
- **boto3** или **aioboto3** — S3-клиент для MinIO.

### Фронтенд
- **Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui**.
- **TanStack Query** для серверного состояния, **zod** для схем, **react-hook-form** для форм.
- Авторизация через httpOnly cookies (refresh) + access JWT в памяти.

### Инфраструктура
- **Docker** + **docker-compose** для локальной разработки (и опционально продакшна).
- **Traefik** — реверс-прокси, TLS, маршрутизация.
- **MinIO** — S3-совместимое хранилище бэкапов/артефактов.
- **Prometheus + Grafana + Loki + Promtail** — метрики, дашборды, логи.
- **GitHub Actions** — CI (lint, types, tests, docker build, push).
- **Ansible** — провижининг нод (роль `node-agent`).

### Тулинг разработки
- **uv** — менеджер зависимостей и виртуального окружения (быстрее Poetry).
- **Ruff** — формат + линт (заменяет black/isort/flake8).
- **mypy --strict** — типы.
- **pytest** + **pytest-asyncio** + **httpx** AsyncClient + **testcontainers-python** — тесты.
- **pre-commit** — хуки.
- **Make** — единый интерфейс команд.

> **Версии:** при `uv add` ставь актуальные на момент создания, не закрепляй жёстко патч-версии — используй `>=X.Y,<X+1`.

---

## 3. Архитектура

Монорепозиторий, четыре деплой-юнита:

```
                     ┌──────────────┐
            HTTPS    │   Traefik    │
   browser ─────────▶│ reverse proxy│
                     └──────┬───────┘
                            │
              ┌─────────────┼──────────────┐
              ▼                            ▼
      ┌───────────────┐            ┌───────────────┐
      │  web (Next.js)│            │  api (FastAPI)│
      └───────────────┘            └───┬───────────┘
                                       │ enqueue (ARQ/Redis)
                                       ▼
                                ┌──────────────┐
                                │   worker     │  ◀── читает задачи
                                │   (ARQ)      │      из Redis
                                └──────┬───────┘
                                       │ HTTP + API key
                                       ▼
                              ┌──────────────────┐
                              │   node-agent     │  ◀── на каждой ноде
                              │ (FastAPI on host)│      управляет Docker
                              └──────────────────┘
                                       │
                                       ▼
                               локальный Docker
                              (контейнеры игр)

   Сквозные: PostgreSQL, Redis, MinIO, Prometheus, Loki, Grafana
```

**Сервисы:**

| Сервис | Назначение |
|---|---|
| `api` | Публичный REST API: auth, users, servers, templates, nodes, audit. |
| `worker` | ARQ-воркер: задачи `provision_server`, `start_server`, `stop_server`, `restart_server`, `delete_server`, `backup_server`, `restore_backup`, `prune_finished`. |
| `node-agent` | Лёгкий FastAPI-сервис на каждой game-ноде. Принимает команды от worker (Bearer API-key + mTLS опционально) и дёргает Docker SDK. **Не имеет доступа к основной БД.** |
| `web` | Next.js фронт. |

**Принципы:**
- API **только** ставит задачи и возвращает состояние из БД. Никаких прямых вызовов Docker из API.
- Worker — единственный, кто знает про ноды и оркестрирует развёртывание.
- Node-agent — тонкая обёртка над Docker SDK, без бизнес-логики.
- Любая операция с инстансом → запись в `audit_log`.
- Все длинные операции возвращают пользователю `task_id`, статус опрашивается / стримится.

---

## 4. Структура репозитория

```
gamehost/
├── apps/
│   ├── api/                      # FastAPI публичное API
│   │   ├── src/gamehost_api/
│   │   │   ├── main.py
│   │   │   ├── api/v1/           # роутеры по доменам
│   │   │   ├── core/             # config, security, deps
│   │   │   ├── db/               # session, models, repositories
│   │   │   ├── domain/           # бизнес-логика (use cases)
│   │   │   ├── schemas/          # Pydantic DTO
│   │   │   └── tasks/            # фасад для постановки ARQ-задач
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   ├── worker/                   # ARQ воркер
│   │   ├── src/gamehost_worker/
│   │   │   ├── main.py           # WorkerSettings
│   │   │   ├── jobs/             # по одной задаче на файл
│   │   │   └── clients/          # node_agent_client, s3_client
│   │   └── ...
│   ├── node_agent/               # FastAPI на ноде
│   │   ├── src/gamehost_node/
│   │   │   ├── main.py
│   │   │   ├── api/              # /containers, /health, /logs/stream
│   │   │   └── docker_ops.py
│   │   └── ...
│   └── web/                      # Next.js
├── packages/
│   └── shared/                   # python-пакет: общие enum, схемы, contracts
│       └── src/gamehost_shared/
├── deploy/
│   ├── docker-compose.yml        # локальная разработка
│   ├── docker-compose.prod.yml
│   ├── traefik/
│   ├── grafana/
│   ├── prometheus/
│   ├── loki/
│   └── ansible/                  # роль node-agent + playbook
├── docs/
│   ├── architecture.md
│   ├── api.md (генерируется)
│   └── runbook.md
├── .github/workflows/
│   ├── ci.yml
│   └── docker.yml
├── .pre-commit-config.yaml
├── Makefile
├── README.md
└── pyproject.toml                # workspace для uv
```

Используй **uv workspace** для монорепы Python-приложений. Каждое приложение — отдельный пакет с своим `pyproject.toml`.

---

## 5. Модель данных (PostgreSQL, ключевые таблицы)

Используй UUID v7 для PK там, где есть user-facing IDs; иначе `bigserial`. Все timestamps — `timestamptz`.

- `users` — `id`, `email` (uniq), `password_hash`, `role` enum (`user`/`admin`), `is_active`, `created_at`.
- `refresh_tokens` — `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `user_agent`, `ip`.
- `nodes` — `id`, `name`, `endpoint_url`, `api_key_hash`, `capacity_cpu`, `capacity_mem_mb`, `status` (`online`/`offline`/`drain`), `last_seen_at`.
- `game_templates` — `id`, `slug` (`minecraft-vanilla`, `cs2`, `valheim`, …), `display_name`, `docker_image`, `default_env` (jsonb), `default_ports` (jsonb), `default_volumes` (jsonb), `min_resources` (jsonb), `is_public`.
- `servers` — `id`, `owner_id`, `name`, `template_id`, `node_id` (nullable до провижининга), `container_id` (nullable), `status` enum (`pending`/`provisioning`/`running`/`stopped`/`failed`/`deleting`), `host`, `port`, `env_overrides` (jsonb), `resources` (jsonb), `created_at`, `updated_at`.
- `server_members` — `server_id`, `user_id`, `role` enum (`viewer`/`operator`), `invited_by`, `created_at`. PK составной.
- `backups` — `id`, `server_id`, `s3_key`, `size_bytes`, `created_by`, `created_at`, `status`.
- `tasks` — `id`, `server_id` (nullable), `kind`, `status`, `payload` (jsonb), `error` (text), `started_at`, `finished_at`. (Зеркало ARQ для UI; ARQ сам по себе не для UI.)
- `audit_log` — `id`, `actor_id`, `action`, `target_type`, `target_id`, `meta` (jsonb), `ip`, `created_at`. Append-only, индекс по `(target_type, target_id, created_at desc)`.

Alembic-миграции пиши через autogenerate, но **проверяй и редактируй** их (autogenerate несовершенен).

---

## 6. REST API (минимальный набор v1)

Префикс `/api/v1`. Ответы — JSON, ошибки — RFC 7807 (`application/problem+json`). OpenAPI должен быть валиден.

**Auth:**
- `POST /auth/register`
- `POST /auth/login` → `{access, refresh-cookie}`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET  /auth/me`

**Templates (read-only для user, CRUD для admin):**
- `GET  /templates`
- `POST /templates` *(admin)*
- `PATCH /templates/{id}` *(admin)*

**Nodes (admin):**
- `GET  /nodes`
- `POST /nodes` — заводит ноду, выдаёт API-ключ (показывает один раз).
- `PATCH /nodes/{id}` — drain/online.
- `DELETE /nodes/{id}`

**Servers:**
- `GET  /servers` — мои + где я member.
- `POST /servers` — `{name, template_id, env_overrides?, resources?}` → 202, `task_id`.
- `GET  /servers/{id}`
- `POST /servers/{id}/start|stop|restart` → 202.
- `PATCH /servers/{id}` — env/конфиг (только когда stopped).
- `DELETE /servers/{id}` → 202.
- `GET  /servers/{id}/logs?tail=200` — последние строки.
- `GET  /servers/{id}/logs/stream` — **SSE** стрим логов (через Redis pub/sub, заполняется node-agent'ом).
- `GET  /servers/{id}/members` / `POST` / `DELETE`.
- `GET  /servers/{id}/backups` / `POST /backups` (создать) / `POST /backups/{id}/restore`.

**Tasks:**
- `GET  /tasks/{id}` — статус.

**Health & meta:**
- `GET  /healthz`, `GET  /readyz`, `GET  /metrics` (Prometheus).

**Node-agent API** (внутренний, Bearer API-key):
- `POST /containers` — создать.
- `POST /containers/{id}/start|stop|restart`.
- `DELETE /containers/{id}`.
- `GET  /containers/{id}` — статус, статистика.
- `GET  /containers/{id}/logs/stream` — SSE.
- `POST /containers/{id}/exec` — для бэкапа: `tar` через docker exec, поток в node-agent → multipart upload в MinIO.
- `GET  /healthz`.

---

## 7. Безопасность

- Пароли — `argon2id`, не bcrypt.
- Access JWT 15 мин, refresh 30 дней, refresh — httpOnly Secure SameSite=Lax cookie, ротация при использовании.
- RBAC: декоратор/Depends `require_role("admin")`, `require_server_role("operator")`.
- Все мутации через `audit_log`.
- Rate-limit на `/auth/*` (используй `slowapi` или собственный middleware на Redis).
- Валидация всех env-overrides по whitelisted-ключам шаблона (никакого `--privileged`, `--cap-add`, `--device`, `bind mount` вне разрешённой директории).
- На node-agent контейнеры запускаются с `--cap-drop=ALL`, `--read-only` где возможно, лимитами CPU/mem из `servers.resources`, в выделенной Docker-сети шаблона.
- Никогда не логируй пароли, токены, API-ключи (фильтр в structlog).
- Все исходящие URL фронтенда — только same-origin или whitelisted; API настраивает CORS строго на домен фронта.

---

## 8. Наблюдаемость

- **Логи:** structlog → JSON в stdout → Promtail → Loki. Поля: `service`, `request_id`, `user_id`, `server_id`, `task_id`.
- **Метрики:** `prometheus-fastapi-instrumentator` для HTTP; кастомные:
  - `gh_servers_total{status=...}`
  - `gh_task_duration_seconds{kind=...}`
  - `gh_node_capacity_used_ratio{node=...}`
  - `gh_arq_jobs_in_flight`, `gh_arq_jobs_failed_total`.
- **Трейсинг:** OpenTelemetry опционально (заведи, но не обязателен в MVP).
- Grafana provisioning: дашборды и datasources как код в `deploy/grafana/`.

---

## 9. Этапы реализации (выполняй по порядку)

> После каждого этапа: `make lint && make typecheck && make test`. Зелёное → коммит → следующий.

**Этап 0 — Скелет.**
1. `uv init` workspace, `apps/*` пакеты, `pyproject.toml` с tool-конфигом (ruff, mypy, pytest).
2. `Makefile` с целями: `install`, `lint`, `format`, `typecheck`, `test`, `up`, `down`, `migrate`, `revision`, `seed`.
3. `pre-commit` (ruff, mypy, end-of-file-fixer, check-merge-conflict).
4. `docker-compose.yml` с Postgres, Redis, MinIO, Traefik, Prometheus, Grafana, Loki, Promtail.
5. CI (`.github/workflows/ci.yml`): на push — install → lint → mypy → test.

**Этап 1 — API: auth + users.**
- Pydantic-settings, async engine, base модели, alembic init, миграция users + refresh_tokens.
- Регистрация/логин/refresh/logout/me. Argon2. JWT.
- Тесты: pytest-asyncio + AsyncClient + testcontainers Postgres. Покрытие auth-флоу.

**Этап 2 — Templates + Nodes (admin CRUD).**
- Сидер `apps/api/scripts/seed_templates.py` с шаблонами для Minecraft (`itzg/minecraft-server`), Valheim (`lloesche/valheim-server`), Terraria, CS2, Rust.
- API-ключ ноды генерируется и хешируется (argon2), отдается один раз.

**Этап 3 — Node-agent (отдельный сервис).**
- FastAPI приложение, Docker SDK.
- Bearer API-key middleware.
- Эндпоинты создания/старта/стопа/удаления контейнера, чтение статистики, SSE логов.
- Dockerfile node-agent монтирует `/var/run/docker.sock`.
- Тесты с testcontainers (запускай настоящий docker-in-docker или мокни Docker SDK).

**Этап 4 — Worker + базовый lifecycle.**
- ARQ `WorkerSettings`, jobs: `provision_server`, `start`, `stop`, `restart`, `delete`.
- Стратегия выбора ноды: простая — наименее загруженная по `capacity_used`.
- Запись в `tasks` и `audit_log`.
- API: `POST /servers`, lifecycle endpoints.
- E2E-тест: создал сервер → задача → агент-мок → статус running.

**Этап 5 — Логи и стрим.**
- Node-agent публикует строки в Redis pub/sub `logs:{container_id}`.
- API SSE-эндпоинт подписывается и стримит клиенту с auth-проверкой.

**Этап 6 — Members & roles.**
- Приглашение по email/токену-ссылке, права `viewer`/`operator`.
- Guard'ы на эндпоинтах сервера.

**Этап 7 — Backups.**
- Job `backup_server`: node-agent запускает `tar` в томе игры, стримит в MinIO multipart upload.
- Job `restore_backup`: обратный поток.
- UI: список бэкапов, кнопка восстановить.

**Этап 8 — Метрики, дашборды, аудит-UI.**
- Все кастомные метрики выставлены.
- Grafana: дашборд «Platform overview», «Server lifecycle», «Worker queue».
- Админ-страница аудита с фильтрами.

**Этап 9 — Frontend (Next.js).**
- Auth flow, server list, server detail (status, logs SSE, env editor с подсветкой YAML/properties), backups, members.
- Админ-секция: nodes, templates, audit.
- Темы light/dark, i18n ru+en.

**Этап 10 — Деплой.**
- `docker-compose.prod.yml` с Traefik labels, certs Let's Encrypt.
- Ansible playbook `node.yml`: ставит docker, кладёт node-agent с systemd unit, прописывает API-ключ через ansible-vault.
- GitHub Actions: build & push образов в GHCR на тег `v*`.
- Runbook в `docs/runbook.md`: как поднять с нуля, как добавить ноду, как откатить.

---

## 10. Конвенции кода

- **Слои:** `api → domain → repository → db`. Роутер не лезет в SQLAlchemy напрямую, идёт через use case.
- **DI** — через `Depends(get_uow)` (Unit of Work) или `Depends(get_session)`.
- **Транзакции** — на уровне use case (`async with uow: ...`).
- **Ошибки:** доменные исключения (`ServerNotFound`, `NodeUnavailable`, `QuotaExceeded`) ловятся одним exception-handler'ом и мапятся в HTTP.
- **Имена:** snake_case в Python, kebab-case в URL, camelCase в JSON (alias через Pydantic `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)`).
- **Логи:** на каждый внешний вызов — `bind` контекста, `info` на старте/успехе, `warning`/`error` с `exc_info=True` на проблеме.
- **Никаких** `print`, `time.sleep`, `requests` (синхронных), `os.system`.
- **Тесты:** unit на доменные правила, integration на репозитории и API через AsyncClient. Используй фабрики (factory-boy/pydantic-factories) вместо хардкода фикстур.

---

## 11. Definition of Done (MVP)

Считается готовым, когда **все** пункты выполняются:

- [ ] `make up` поднимает весь стек локально, фронт открывается на `https://gamehost.localhost` (через Traefik + локальный CA).
- [ ] Можно зарегистрироваться, создать сервер Minecraft, увидеть `running`, подключиться клиентом, остановить, удалить.
- [ ] Логи Minecraft-сервера стримятся в UI в реальном времени.
- [ ] Бэкап создаётся и восстанавливается, файл лежит в MinIO.
- [ ] Админ может добавить вторую ноду; новый сервер уходит на менее загруженную.
- [ ] Все эндпоинты покрыты тестами; общее покрытие ≥ 70%, на `domain/` ≥ 85%.
- [ ] `ruff check`, `mypy --strict`, `pytest` — зелёные в CI.
- [ ] OpenAPI-схема экспортируется в `docs/openapi.json` и валидна.
- [ ] Dashboard «Platform overview» показывает живые метрики.
- [ ] README объясняет: запуск, env, миграции, добавление ноды, troubleshooting.
- [ ] `docs/architecture.md` содержит C4 (Context + Container) диаграммы и таблицу решений (ADR-light).

---

## 12. Чего НЕ делаем в MVP

- Биллинг, платежи, тарифы.
- Мобильное приложение.
- Мульти-регион / геораспределение.
- Авто-скейлинг нод (пользователь добавляет ноды вручную).
- Сложный UI редактор `server.properties` со всеми настройками — достаточно сырого текстового редактора + валидация.
- gRPC между сервисами (закладывайся на возможность миграции, но не реализуй).

---

## 13. Старт

Первое сообщение от тебя в ответ на этот промпт должно содержать:
1. Список из 3–7 уточняющих вопросов (если есть). Если их нет — явно скажи «вопросов нет».
2. Подтверждение плана этапов и того, с какого ты начнёшь.
3. **Никакого кода** до моего «ок».

После «ок» — начинай с Этапа 0.
