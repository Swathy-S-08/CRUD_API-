import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response


app = FastAPI(title="Task Management API")

DB_PATH = Path(__file__).with_name("tasks.db")

INITIAL_TASKS = [
    ("Buy milk", False),
    ("Finish assignment", False),
    ("Read a book", True),
]


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with closing(get_connection()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        task_count = connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

        if task_count == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [(title, int(done)) for title, done in INITIAL_TASKS],
            )

        connection.commit()


@app.on_event("startup")
def startup():
    initialize_database()


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


def task_not_found(task_id):
    return JSONResponse(
        status_code=404,
        content={"error": f"task {task_id} not found"},
    )


@app.get("/")
def root():
    return {"message": "Task Management API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/tasks")
async def create_task(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "title is required"},
        )

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "title is required"},
        )

    done = data.get("done", False)

    if not isinstance(done, bool):
        return JSONResponse(
            status_code=400,
            content={"error": "done must be a boolean"},
        )

    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title.strip(), int(done)),
        )

        task_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return JSONResponse(
        status_code=201,
        content=row_to_task(row),
    )


@app.get("/tasks")
def get_tasks():
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id"
        ).fetchall()

    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    if row is None:
        return task_not_found(task_id)

    return row_to_task(row)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid request body"},
        )

    if "title" in data:
        title = data["title"]

        if not isinstance(title, str) or not title.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "title is required"},
            )

    if "done" in data and not isinstance(data["done"], bool):
        return JSONResponse(
            status_code=400,
            content={"error": "done must be a boolean"},
        )

    with closing(get_connection()) as connection:
        existing_task = connection.execute(
            "SELECT id FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if existing_task is None:
            return task_not_found(task_id)

        if "title" in data:
            connection.execute(
                "UPDATE tasks SET title = ? WHERE id = ?",
                (data["title"].strip(), task_id),
            )

        if "done" in data:
            connection.execute(
                "UPDATE tasks SET done = ? WHERE id = ?",
                (int(data["done"]), task_id),
            )

        connection.commit()

        updated_task = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return row_to_task(updated_task)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )

        if cursor.rowcount == 0:
            return task_not_found(task_id)

        connection.commit()

    return Response(status_code=204)
