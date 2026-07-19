from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task Management API")


class Task(BaseModel):
    id: int
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str
    completed: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


tasks = [
    Task(id=1, title="Buy milk", completed=False),
    Task(id=2, title="Finish assignment", completed=False),
    Task(id=3, title="Read a book", completed=True),
]

next_task_id = 4


def find_task(task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail={"error": f"task {task_id} not found"}
    )


@app.get("/tasks", response_model=list[Task])
def get_tasks():
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    return find_task(task_id)


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task_data: TaskCreate):
    global next_task_id

    task = Task(
        id=next_task_id,
        title=task_data.title,
        completed=task_data.completed,
    )

    tasks.append(task)
    next_task_id += 1

    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_data: TaskUpdate):
    task = find_task(task_id)

    if task_data.title is not None:
        task.title = task_data.title

    if task_data.completed is not None:
        task.completed = task_data.completed

    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def partially_update_task(task_id: int, task_data: TaskUpdate):
    task = find_task(task_id)

    if task_data.title is not None:
        task.title = task_data.title

    if task_data.completed is not None:
        task.completed = task_data.completed

    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    task = find_task(task_id)
    tasks.remove(task)

    return {"message": f"task {task_id} deleted successfully"}
