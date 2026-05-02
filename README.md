# cust_dev_ai

Async Python backend for AI-powered customer development interviews. Generates
user personas and simulated custdev interviews via LangGraph agents, manages
interviews and tasks, and exposes a RESTful API via FastAPI.

## System Context

This repository is the main product backend in a multi-service system.

Related service:

- `/home/vito_brat/ml_service` — internal ML/vector-search microservice. It owns
  Qdrant vector storage, Triton-based embedding generation, semantic search,
  and RabbitMQ handlers for `embeddings.request` and `search.request`.

Boundary between services:

- `cust_dev_ai` owns product entities, user/interview/persona workflows,
  PostgreSQL state, Redis task tracking, simulated-interview persistence, and
  LLM/LangGraph orchestration.
- `ml_service` owns vector database and RAG retrieval infrastructure.
- The intended integration mechanism is RabbitMQ request/reply.

Current code status: this service contains a generic RabbitMQ client and
RabbitMQ configuration, but no source-level calls to `ml_service` queues
(`embeddings.request`, `search.request`) were found during the 2026-04-25 code
pass. Treat the concrete end-to-end RAG producer flow as planned or external
until producer code is added here.

## Documentation Map

- `README.md`: project overview, setup, API, and system context.
- `PROJECT_CONTEXT.md`: local bootstrap context for future AI agents.
- `AGENTS.md`: local Codex prompt; currently ignored by `.gitignore`.
- `/home/vito_brat/ml_service/PROJECT_CONTEXT.md`: companion vector-search
  service context.
- `/home/vito_brat/ml_service/ARCHITECTURE.md`: detailed vector-search
  architecture and RabbitMQ boundary.

## Tech Stack

- **Web**: FastAPI 0.135, Uvicorn, Slowapi (rate limiting)
- **AI/LLM**: LangChain 1.2, LangGraph 1.0, Instructor 1.14 (structured outputs), Langfuse 3.12 (observability)
- **LLM Provider**: OpenRouter (configurable, dev default: `qwen/qwen3.5-27b`)
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic
- **DI**: dependency-injector 4.48
- **Config**: OmegaConf + Pydantic Settings
- **Testing**: pytest, testcontainers, polyfactory

## Architecture

The project follows **Domain-Driven Design** with a three-layer **Dependency Injection** container hierarchy:

```
RootContainer
├── InfrastructureContainer  — DatabaseClient, LLMAdapter, Langfuse
└── DomainContainer          — per-domain containers (repo, service, graphs)
```

### Domains

| Domain | Table | Description |
|---|---|---|
| `user` | `users` | Root entity; owns interviews and tasks |
| `interview` | `interviews` | Customer development interview and simulation orchestration |
| `persona` | `personas` | AI-generated user segment (with JSONB demographic state) |
| `sub_interview` | `sub_interviews` | Persisted simulated dialogue session inside an interview |
| `task` | `tasks` | Background job tracking (progress, status, error log) |

Each domain contains:

- `db/postgres/{model.py, repository.py}` — ORM model and CRUD repository
- `app/requests/{router.py, schema.py}` — FastAPI router and request/response schemas
- `app/usecases/service.py` — Application service (business logic)
- `exceptions.py` — Domain-specific exceptions

The `persona` and `interview` domains additionally have:

- `infrastructure/graph/` — LangGraph agents
- `infrastructure/prompt/` — Prompt templates and manager

### LangGraph Persona Generation Pipeline

```
UserSegmentSearchGraph
    → finds and verifies a user segment from input

GeneratePersonasGraph  (map-reduce)
    → maps N personas to N GenerateSinglePersonaGraph sub-graph calls

GenerateSinglePersonaGraph
    → generates demographic attributes, biography, and experiences in parallel
    → combines into a structured PersonaSchema
```

### LangGraph Interview Simulation Pipeline

```
InterviewOrchestratorGraph
    → generates compact industry context from the task input
    → runs PreInterviewPreparationGraph once
    → runs InterviewSimulationGraph in bounded persona batches
    → runs PostInterviewUpdateGraph after each batch
    → returns all per-persona interview reports and final interview plan

PreInterviewPreparationGraph
    → studies segment and industry context
    → performs parallel concern/risk/goal/ideal-result analysis
    → produces the pre-interview plan

InterviewSimulationGraph
    → generates interviewer questions
    → generates simulated persona answers
    → preserves validator notes before final analysis
    → produces one interview report and full dialogue history

PostInterviewUpdateGraph
    → updates the pre-interview plan from the latest batch reports only
```

All graphs extend `BaseGraph` (`src/infrastructure/graph/base_graph.py`),
which wraps LangGraph's `StateGraph` and injects `LLMAdapter` and
`BasePromptManager`.

### API Endpoints

All endpoints follow the same response envelope:

```json
{ "msg": <data_or_null>, "status": "success|error", "details": "<error_message_or_null>" }
```

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/users/` | Create user |
| GET | `/api/v1/users/` | List users (paginated) |
| GET | `/api/v1/users/count` | Count users |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PUT | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Delete user |
| POST | `/api/v1/interviews/` | Create interview |
| GET | `/api/v1/interviews/` | List interviews (paginated) |
| GET | `/api/v1/interviews/count` | Count interviews |
| GET | `/api/v1/interviews/{id}` | Get interview by ID |
| PUT | `/api/v1/interviews/{id}` | Update interview |
| DELETE | `/api/v1/interviews/{id}` | Delete interview |
| POST | `/api/v1/personas/` | Create persona (triggers LangGraph pipeline) |
| GET | `/api/v1/personas/` | List personas (paginated) |
| GET | `/api/v1/personas/count` | Count personas |
| GET | `/api/v1/personas/{id}` | Get persona by ID |
| PUT | `/api/v1/personas/{id}` | Update persona |
| DELETE | `/api/v1/personas/{id}` | Delete persona |
| POST | `/api/v1/sub_interviews/` | Create sub-interview |
| GET | `/api/v1/sub_interviews/` | List sub-interviews (paginated) |
| GET | `/api/v1/sub_interviews/count` | Count sub-interviews |
| GET | `/api/v1/sub_interviews/{id}` | Get sub-interview by ID |
| PUT | `/api/v1/sub_interviews/{id}` | Update sub-interview |
| DELETE | `/api/v1/sub_interviews/{id}` | Delete sub-interview |
| POST | `/api/v1/tasks/` | Create task |
| GET | `/api/v1/tasks/` | List tasks (paginated) |
| GET | `/api/v1/tasks/count` | Count tasks |
| GET | `/api/v1/tasks/{id}` | Get task by ID |
| PUT | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |
| POST | `/api/v1/tasks/personas_pipeline_task` | Register persona pipeline task in Redis |
| POST | `/api/v1/tasks/generate_single_persona_task` | Register single-persona generation task in Redis |
| POST | `/api/v1/tasks/generate_personas_task` | Register batch persona generation task in Redis |
| POST | `/api/v1/tasks/interview_simulation_task` | Register full interview simulation task in Redis |

## Configuration

App config is loaded from `config/config.dev.yaml` (override with `CONFIG_PATH` env var).

### `config/config.dev.yaml`

```yaml
app_host: "0.0.0.0"
app_port: 8000
log_level: "DEBUG"
workers_number: 1

persona:
  graph_recursion_limit: 100

interview:
  recursion_limit: 10
  simulation_recursion_limit: 80

postgres:
  pool_size: 5
  max_overflow: 10
  echo: false

redis:
  host: redis
  port: 6379
  db: 0
  max_connections: 10

rabbitmq:
  host: "rabbitmq"
  port: 5672
  vhost: "ml"

llm:
  model_name: "qwen/qwen3.5-27b"
  base_url: "https://openrouter.ai/api/v1"
  temperature: 0.1
  max_tokens: 4096
```

### Required Environment Variables (`config/.env`)

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=5432
POSTGRES_DB=

REDIS_PASSWORD=

RABBITMQ_USER=
RABBITMQ_PASSWORD=

LANGFUSE_BASE_URL=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=

LLM_API_KEY=
```

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Python 3.12+ (for local development)
- Poetry 2.0+

### Run with Docker Compose

```bash
# Start PostgreSQL + Redis + app + Redis worker
make up

# View logs
make logs

# Stop
make down
```

### Run Locally

```bash
# Install dependencies
poetry install

# Activate virtual environment
source .venv/bin/activate

# Apply DB migrations
make roll_up_migrations

# Start FastAPI server (reads config/config.dev.yaml)
make run
```

## Database Migrations

```bash
# Generate a new migration (validate the output before applying)
make add_migration

# Apply pending migrations
make roll_up_migrations
```

Alembic `env.py` auto-discovers all `model.py` files under `src/` to populate metadata.

## Development Commands

```bash
make up                  # Start dev environment (Docker Compose)
make down                # Stop dev environment
make run                 # Run FastAPI server locally
make logs                # View live application logs
make tests               # Run all tests
make unit                # Run unit tests only
make integration         # Run integration tests only
make lint                # Run pre-commit hooks on all files
make install-lint        # Install pre-commit hooks
make add_migration       # Generate a new Alembic migration
make roll_up_migrations  # Apply migrations to the database
```

### Run a Single Test

```bash
# Single file
python3 -m pytest -vv tests/path/to/test_file.py

# Single test by name
python3 -m pytest -vv tests/path/to/test_file.py::test_function_name
```

## Testing

- **Integration tests** use `testcontainers` (PostgreSQL 16 Alpine); migrations
  are applied once per session, each test runs in a rolled-back transaction.
- **Test data** is generated via `polyfactory` (`ModelFactory`).
- **LLM is always mocked** via an `autouse` fixture (`override_llm`) that
  overrides `container.infrastructure.llm`; no real API calls in tests.
- **Factory fixtures**: `*_factory` creates entities on demand; plain `*`
  fixtures (e.g. `user`, `persona`) create a single ready entity.

## Code Style

| Tool | Purpose | Config |
|---|---|---|
| `black` | Formatting | `pyproject.toml` |
| `ruff` | Fast linting | `pyproject.toml` |
| `isort` | Import sorting (wemake profile) | `setup.cfg` |
| `flake8` + `wemake-python-styleguide` | Style enforcement | `setup.cfg` |
| `mypy` | Strict type checking | `setup.cfg` |

Key limits: line length 120, max complexity 8, max arguments 10, max methods 12, max module members 10.

All functions must have full type hints. `mypy` runs in strict mode.

## Project Structure

```
cust_dev_ai/
├── config/
│   ├── .env                         # Secrets (not committed)
│   ├── config.dev.yaml              # App configuration
│   └── logging.yaml                 # Logging configuration
├── docker/
│   ├── Dockerfile                   # Multi-stage build (dev/prod)
│   └── docker-compose.dev.yaml      # PostgreSQL 16 + FastAPI app
├── src/
│   ├── app.py                       # FastAPI entry point (lifespan, routers)
│   ├── configs/                     # Pydantic config classes + constants
│   ├── schemas/                     # Centralized Pydantic schemas per domain
│   ├── infrastructure/
│   │   ├── containers/              # DI containers (root, infrastructure, domain)
│   │   ├── db/postgres/             # Base ORM model, client, CRUD repository ABC
│   │   ├── graph/                   # BaseGraph (LangGraph wrapper)
│   │   ├── llm/                     # LLMAdapter (Instructor + LangChain fallback)
│   │   └── prompt/                  # BasePromptManager
│   └── domains/
│       ├── user/
│       ├── interview/               # + LangGraph interview simulation agents + prompt templates
│       ├── persona/                 # + LangGraph agents + prompt templates
│       ├── sub_interview/
│       └── task/
├── tests/
│   ├── conftest.py                  # Global fixtures (DB, containers, LLM mock)
│   ├── unit/
│   └── integration/
├── Makefile
├── pyproject.toml
├── setup.cfg
├── alembic.ini
└── pytest.ini
```
