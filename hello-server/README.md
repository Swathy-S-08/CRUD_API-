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


## AI vs me

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