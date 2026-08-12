import os
from contextlib import asynccontextmanager, closing

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "tasks")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD is not set")


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def initialize_database():
    with closing(get_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )

            cursor.execute("SELECT COUNT(*) FROM tasks")
            task_count = cursor.fetchone()[0]

            if task_count == 0:
                cursor.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    [
                        ("Buy milk", False),
                        ("Finish assignment", False),
                        ("Read a book", True),
                    ],
                )

        connection.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    lifespan=lifespan,
)


def row_to_task(row):
    return {
        "id": row[0],
        "title": row[1],
        "done": row[2],
    }


def task_not_found(task_id: int):
    return JSONResponse(
        status_code=404,
        content={"error": f"task {task_id} not found"},
    )


@app.get("/")
def root():
    return {
        "name": "Task Management API",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    try:
        with closing(get_connection()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {"status": "healthy"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"},
        )


@app.get("/tasks")
def get_tasks():
    with closing(get_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks ORDER BY id"
            )
            rows = cursor.fetchall()

    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with closing(get_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s",
                (task_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return task_not_found(task_id)

    return row_to_task(row)


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
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done
                """,
                (title.strip(), done),
            )
            row = cursor.fetchone()

        connection.commit()

    return JSONResponse(
        status_code=201,
        content=row_to_task(row),
    )


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
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM tasks WHERE id = %s",
                (task_id,),
            )

            if cursor.fetchone() is None:
                return task_not_found(task_id)

            if "title" in data:
                cursor.execute(
                    "UPDATE tasks SET title = %s WHERE id = %s",
                    (data["title"].strip(), task_id),
                )

            if "done" in data:
                cursor.execute(
                    "UPDATE tasks SET done = %s WHERE id = %s",
                    (data["done"], task_id),
                )

            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s",
                (task_id,),
            )
            row = cursor.fetchone()

        connection.commit()

    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with closing(get_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s",
                (task_id,),
            )

            if cursor.rowcount == 0:
                return task_not_found(task_id)

        connection.commit()

    return Response(status_code=204)
