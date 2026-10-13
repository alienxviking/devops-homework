import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import load_config

settings = load_config()
app = FastAPI(title=settings["app_name"], version=os.getenv("APP_VERSION", "dev"))


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class Task(TaskIn):
    id: int


tasks: dict[int, Task] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return list(tasks.values())


@app.post("/tasks", status_code=201)
def create_task(task: TaskIn):
    if len(tasks) >= settings["max_tasks"]:
        raise HTTPException(status_code=429, detail="task limit reached")
    new_id = max(tasks, default=0) + 1
    tasks[new_id] = Task(id=new_id, **task.model_dump())
    return tasks[new_id]


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskIn):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="task not found")
    tasks[task_id] = Task(id=task_id, **task.model_dump())
    return tasks[task_id]


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if tasks.pop(task_id, None) is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"deleted": task_id}
