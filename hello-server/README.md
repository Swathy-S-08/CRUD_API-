# Task API

A simple CRUD API for managing tasks, built with FastAPI as part of the FlyRank AI Internship.

## What this is

A REST API with an in-memory task list supporting full CRUD operations (Create, Read, Update, Delete), input validation, and interactive documentation via Swagger UI.

## How to run it

```bash
git clone https://github.com/Swathy-S-08/CRUD_API-.git
cd CRUD_API-/hello-server
python -m venv venv
venv\Scripts\activate        # Windows
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
```

Then visit `http://localhost:8000`.

## Endpoints

| Method | Endpoint         | Description                          | Success | Error                     |
|--------|------------------|---------------------------------------|---------|----------------------------|
| GET    | `/`              | API info                              | 200     | —                          |
| GET    | `/health`        | Health check                          | 200     | —                          |
| GET    | `/tasks`         | List all tasks                        | 200     | —                          |
| GET    | `/tasks/{id}`    | Get a single task                     | 200     | 404 if not found           |
| POST   | `/tasks`         | Create a task (`{"title": "..."}`)    | 201     | 400 if title missing/empty |
| PUT    | `/tasks/{id}`    | Update a task's title and/or done     | 200     | 404 if not found, 400 if title invalid |
| DELETE | `/tasks/{id}`    | Delete a task                         | 204     | 404 if not found           |

## Example request

```
curl -i http://localhost:8000/tasks/1
```

```
HTTP/1.1 200 OK
date: Sun, 19 Jul 2026 15:27:04 GMT
server: uvicorn
content-length: 44
content-type: application/json

{"id":1,"title":"Learn FastAPI","done":true}
```

## Interactive docs

FastAPI auto-generates Swagger UI at `/docs`:

![Swagger UI](screenshots/swagger.png)


## AI vs me - Assignment 1

### My prompt (first attempt)

Build a REST API in Python using FastAPI with an in-memory list of tasks. Each task has an id, title, and a boolean done field, pre-filled with 3 example tasks. Include: GET /tasks to list all tasks, GET /tasks/{id} to get one task (404 with a JSON error if not found), POST /tasks to create a task from a JSON body (400 with a JSON error if title is missing or empty), PUT /tasks/{id} to update a task's title and/or done status (404 if not found), and DELETE /tasks/{id} to remove a task, returning 204 with no body. Enable Swagger UI docs.

### What the AI did better

The AI used Pydantic models (`Task`, `TaskCreate`, `TaskUpdate`) as real class-based schemas instead of raw dicts, and factored the repeated "find task or 404" logic into one `find_task()` helper instead of the loop I copy-pasted into three endpoints. I understand this well enough to explain it: Pydantic validates incoming JSON shape automatically before the function body runs, and centralizing `find_task()` means the 404 check only has to be written and maintained once.

### What it got wrong or ignored

- **404 error shape is nested, not flat.** `GET /tasks/99` returned:

HTTP/1.1 404 Not Found
{"detail":{"error":"task 99 not found"}}
  I asked for a flat `{"error": "..."}`. FastAPI's `HTTPException(detail=...)` always wraps whatever you pass inside a `"detail"` key, so `detail={"error": ...}` produces this extra nesting.

- **POST with missing title returns 422, not 400.** Posting `{}` to `/tasks` returned:
HTTP/1.1 422 Unprocessable Content
{"detail":[{"type":"missing","loc":["body","title"],"msg":"Field required",...}]}
  I asked for `400`. Because the AI made `title: str` required directly on the Pydantic model, FastAPI intercepts the request before the function body runs and auto-returns its own `422` — it never wrote a hand-checked `400` like I did.

- **DELETE returns 200 with a body, not 204 with an empty body.**
HTTP/1.1 200 OK
{"message":"task 1 deleted successfully"}
  I was explicit about `204 No Content` with an empty body.

- **Missing endpoints.** I forgot to mention `GET /` and `GET /health` in this prompt, so the AI didn't build them — a gap in my prompt, not the AI's fault.

- **Unrequested extra endpoint.** The AI added `PATCH /tasks/{id}`, duplicating the PUT logic exactly, which I never asked for.

- **Field name mismatch.** The AI used `completed` instead of `done`.

### What my prompt forgot to specify — and what the AI silently decided

I never specified the exact JSON shape for error bodies, so the AI defaulted to FastAPI's built-in `HTTPException`/`detail` convention. I didn't say "only build these five endpoints," so it added an unrequested `PATCH`. And I didn't pin down the exact field name, so it picked `completed` over `done` — a reasonable but silent decision that would break any client written against my original spec.

### The rematch

I rewrote my prompt to explicitly specify: the field name `done` (not `completed`), a flat error shape `{"error": "..."}` instead of FastAPI's default `detail` wrapper, that a missing/empty title must return a hand-checked `400` rather than Pydantic's automatic `422`, that DELETE must return `204` with an empty body, and that no endpoints beyond the five CRUD routes should be added.

**What changed:** nothing — the regenerated code was byte-for-byte identical to the first attempt, down to the same field name, same nested error shape, same extra `PATCH` endpoint, and same `200` on delete. My more precise prompt had no effect on the output, which was the most interesting result of this stage: it suggests the AI tool reused/anchored to its earlier answer rather than genuinely re-reasoning from the new prompt, and it's a reminder that "asked more precisely" doesn't automatically mean "got a different or better answer" — regeneration behavior matters as much as prompt wording.


## AI vs me — Assignment 2 (SQLite migration)

### My prompt (first attempt)

Migrate a FastAPI in-memory task API to use a SQLite database. Store tasks in a file called task.db, with a tasks table containing id, title, and a boolean done column. Create the table if it doesn't exist, and seed three example tasks only if the table is empty. Keep the same five CRUD endpoints (GET /tasks, GET /tasks/{id}, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}) with identical behavior to before: 400 for a missing/empty title, 404 for an unknown id, 201 on create, 204 on delete. Use parameterized queries for all SQL.

### What the AI did better

It used a `closing()` context manager around every database connection, guaranteeing the connection closes even if an error occurs mid-request — more robust than my manual `conn.close()` calls, which could get skipped if an exception happened first. It also factored row-to-JSON conversion and 404 handling into small reusable helper functions (`row_to_task()`, `task_not_found()`) instead of repeating that logic in every endpoint like I did. Most notably, it added strict type validation on the `done` field — rejecting a request where `done` isn't actually a boolean (e.g. a string like `"yes"`) with a `400`. My hand-built version never checks this at all; it would silently accept and store garbage into that column.

### What it got wrong or quietly ignored

- **Database filename typo, carried through faithfully.** I mistyped `task.db` instead of `tasks.db` in my prompt, and the AI didn't catch or question it — it just built the whole app around the wrong filename, creating a completely separate database file from my hand-built version.
- **Missing `GET /` and `GET /health`.** I forgot to mention these in my first prompt, so the AI didn't include them — same gap as my A1 rematch.
- **Unrequested `PATCH /tasks/{id}` endpoint**, duplicating `PUT`'s logic exactly, which I never asked for — same pattern as the AI added in my A1 rematch too.

### What my prompt forgot to specify — and what the AI silently decided

I never specified the exact JSON error message text or capitalization, so the AI used its own lowercase phrasing (`"task 1 not found"`) rather than matching my hand-built version's wording. I also didn't explicitly restrict the AI to *only* the five CRUD routes plus root/health, so it added the extra `PATCH` route on its own initiative — a reasonable REST convention, but not something I asked for. And the `task.db` typo is really on me, not a silent AI decision — but it's a good demonstration of how literally an AI will follow a spec, typos and all, with no pushback.

### The rematch

I corrected my prompt to say: use the exact filename `tasks.db`, include `GET /` and `GET /health`, and build only the five CRUD routes plus those two — no PATCH or any other extra endpoint.

**What changed:** all three issues were fixed exactly as requested — the database file is now `tasks.db`, both `GET /` and `GET /health` are present, and the unrequested `PATCH` endpoint was removed. Everything else (the helper functions, the `closing()` pattern, the strict boolean validation) stayed the same between generations, since I didn't ask for those to change. This rematch went noticeably better than my A1 rematch, where the regenerated code was identical to the first attempt despite a more detailed prompt — here, the AI clearly incorporated every specific correction I made.


## Database

This project uses **SQLite** for storage — chosen because it's a single file (`tasks.db`), requires zero setup or separate server, and means your data survives a server restart, unlike the in-memory version from Assignment 1.

`tasks.db` is created automatically the first time the app runs — it's git-ignored, so each fresh clone starts with its own freshly seeded database (3 example tasks).

## How to run it

```bash
git clone https://github.com/Swathy-S-08/CRUD_API-.git
cd CRUD_API-/hello-server
python -m venv venv
venv\Scripts\activate        # Windows
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
```

Then visit `http://localhost:8000`. `tasks.db` and its table are created automatically on first run, seeded with 3 example tasks.

## Database screenshot

![Database in DB Browser](screenshots/db-browser.png)

## Example SQL query (from Stage 4)

```sql
SELECT COUNT(*) FROM tasks;
```

This returned `3`, confirming the seed data was still intact and hadn't duplicated across restarts. After running an `UPDATE tasks SET done = 1;` and clicking "Write Changes" in DB Browser, calling `GET /tasks` on my running API immediately showed all tasks marked as done — no restart needed, since the API and DB Browser read the exact same `tasks.db` file.