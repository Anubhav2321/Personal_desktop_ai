from fastapi import APIRouter
from pydantic import BaseModel
from ..database import tasks_collection

router = APIRouter()

class TaskRequest(BaseModel):
    task: str

@router.post("/add-task")
async def add_task(request: TaskRequest):
    if tasks_collection is None:
        return {"status": "error", "message": "Database not available."}
    new_task = {"task": request.task, "status": "pending"}
    tasks_collection.insert_one(new_task)
    return {"status": "success", "message": "Task added to ARIS database."}

@router.get("/get-tasks")
async def get_tasks():
    if tasks_collection is None:
        return {"tasks": []}
    tasks = list(tasks_collection.find({}, {"_id": 0}))
    return {"tasks": tasks}