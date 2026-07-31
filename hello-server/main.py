from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3

DB_FILE = "tasks.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Learn FastAPI", 0),
                ("Build a CRUD API", 0),
                ("Push to GitHub", 1),
            ]
        )

    conn.commit()
    conn.close()

init_db()

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

    result = [dict(row) for row in rows]
    return result

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Returns a single task by id, from the database. 404 if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
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
        "INSERT INTO tasks (title,done) VALUES (?, ?)",
        (task.title,0)
    )

    conn.commit()
    new_id=cursor.lastrowid
    conn.close()

    new_task={"id":new_id,"title":task.title,"done":False}

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

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing=cursor.fetchone()

    if existing is None:
        conn.close()
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    new_title = update.title if update.title is not None else existing["title"]
    new_done = int(update.done) if update.done is not None else existing["done"]

    cursor.execute(
        "UPDATE tasks SET title=?, done=? WHERE id=?",
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

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing=cursor.fetchone()

    if existing is None:
            conn.close()
            return JSONResponse(
                status_code=404,
                content={"error": "Task not found"}
            )

    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

    return Response(status_code=204)