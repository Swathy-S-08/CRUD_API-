
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import psycopg
import os
from dotenv import load_dotenv
from supabase import create_client, Client   # NEW

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")     # NEW
SUPABASE_KEY = os.getenv("SUPABASE_KEY")     # NEW

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)   # NEW

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")

def get_connection():
    conn = psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()["count"]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("Learn FastAPI", False),
                ("Build a CRUD API", False),
                ("Push to GitHub", True),
            ]
        )

    conn.commit()
    conn.close()

#init_db()  commented out for A4 — don't need Postgres running for auth work

app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing tasks.",
    version="1.0"
)



class TaskCreate(BaseModel):
    title: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/")
def read_root():
    """Returns basic info about this API."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    """Health check endpoint — confirms the server is running."""
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    """Returns the full list of tasks, read from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    conn.close()

    return rows

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Returns a single task by id, from the database. 404 if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    return dict(row)


@app.post("/tasks")
def create_task(task: TaskCreate):
    """Creates a new task. Requires a non-empty title. Returns 201 on success."""
    if not task.title or not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"}
        )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title,done) VALUES (%s, %s) RETURNING *",
        (task.title,False)
    )

    new_task=cursor.fetchone()
    conn.commit()
    conn.close()

    return JSONResponse(
        status_code=201,
        content=new_task
    )

@app.put("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    """Updates a task's title and/or done status. 404 if the task doesn't exist."""
    if update.title is not None and not update.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    existing=cursor.fetchone()

    if existing is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    new_title = update.title if update.title is not None else existing["title"]
    new_done = update.done if update.done is not None else existing["done"]

    cursor.execute(
        "UPDATE tasks SET title=%s, done=%s WHERE id=%s",
        (new_title, new_done, task_id)
    )

    conn.commit()
    conn.close()

    updated_task = {"id": task_id, "title": new_title, "done": bool(new_done)}
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Deletes a task by id. Returns 204 on success, 404 if not found."""
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    existing=cursor.fetchone()

    if existing is None:
            conn.close()
            return JSONResponse(
                status_code=404,
                content={"error": "Task not found"}
            )

    cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit()
    conn.close()

    return Response(status_code=204)