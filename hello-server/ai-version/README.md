# Task Management API

A single-file FastAPI REST API backed by PostgreSQL and fully containerized with Docker.

## Files

- `main.py` — the complete FastAPI application
- `Dockerfile` — API container image
- `compose.yaml` — FastAPI + PostgreSQL stack
- `.env.example` — environment-variable template
- `.env` — local environment values
- `requirements.txt` — pinned Python dependencies
- `.gitignore` — prevents `.env` from being committed

## Start

Make sure `.env` contains your PostgreSQL password, then run:

```bash
docker compose up --build
```

The API is available at:

```text
http://localhost:8000
```

## Endpoints

- `GET /` — basic API information
- `GET /health` — database-backed health check
- `GET /tasks` — get all tasks
- `GET /tasks/{id}` — get one task
- `POST /tasks` — create a task
- `PUT /tasks/{id}` — update a task
- `DELETE /tasks/{id}` — delete a task

## Behavior

- Missing or empty `title` returns HTTP `400`.
- Unknown task IDs return HTTP `404` with `{"error": "task <id> not found"}`.
- Successful creation returns HTTP `201`.
- Successful deletion returns HTTP `204` with no response body.
- Three starter tasks are inserted only when the `tasks` table is empty.
- All SQL that uses application/user values is parameterized.

## Persistence

PostgreSQL uses the named Docker volume `postgres_data`.

Removing and recreating the database container does not remove this volume:

```bash
docker compose down
docker compose up --build
```

Do **not** use `docker compose down -v` if you want to preserve the database volume.
