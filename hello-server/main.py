from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional


app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing tasks.",
    version="1.0"
)

tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Push to GitHub", "done": True},
]

class TaskCreate(BaseModel):
    title: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str]=None
    done: Optional[bool]=None

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
    """Returns the full list of tasks."""
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id:int):
    """Returns a single task by id. 404 if it doesn't exist."""
    for task in tasks:
        if task["id"]==task_id:
            return task
        return JSONResponse(
            status_code=404,
            content={"error":f"Task {task_id} not found"}
        )
    

@app.post("/tasks")
def create_task(task: TaskCreate):
    """Creates a new task. Requires a non-empty title. Returns 201 on success."""
    if not task.title or not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required"}
        )

    next_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {"id": next_id, "title": task.title, "done": False}
    tasks.append(new_task)

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

    for task in tasks:
        if task["id"] == task_id:
            if update.title is not None:
                task["title"] = update.title
            if update.done is not None:
                task["done"] = update.done
            return task

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Deletes a task by id. Returns 204 on success, 404 if not found."""
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return Response(status_code=204)

    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"}
    )