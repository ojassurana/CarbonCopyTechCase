from fastapi import FastAPI, BackgroundTasks
import uvicorn
import asyncio
import random
import openai
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
tasks = {}  # In-memory storage for tasks (task_id -> status)


async def run_test_in_background(task_id: str, url: str):
    # Placeholder for test outcome
    outcome = random.choice(["failed", "passed"])
    tasks[task_id] = {"status": outcome, "details": f"Test result for {url}"}


# For the user to submit URL for testing. 
@app.post("/test/{task_id}")
async def start_test(task_id: str, url: str, background_tasks: BackgroundTasks):
    if task_id in tasks:
        return {"status": "Task ID Already exists"}
    tasks[task_id] = {"status": "pending"}
    background_tasks.add_task(run_test_in_background, task_id, url)
    return {"status": "pending"}

# For the user to retrieve test results
@app.get("/result/{task_id}")
async def get_result(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] == "pending":
        return {"status": "pending"}
    return {"status": task["status"], "details": task.get("details", {})}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)