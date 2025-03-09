from fastapi import FastAPI, BackgroundTasks
import uvicorn
import asyncio
import random
import openai
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import os
load_dotenv()

app = FastAPI()
tasks = {}  # In-memory storage for tasks (task_id -> status)


async def run_test_in_background(task_id: str, url: str):
    os.makedirs("screenshots", exist_ok=True)  # Ensure the screenshots directory exists
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://video-converter.com/")
        await page.wait_for_load_state("networkidle")
        
        async def on_dialog(dialog):
            await dialog.accept(url)
            await page.wait_for_timeout(10000)
            screenshot_path = f"screenshots/{task_id}.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved at {screenshot_path} for task_id: {task_id}")
        
        page.on("dialog", on_dialog)
        
        await page.click("text=URL")
        print(f"Clicked on URL button for task_id: {task_id}")
        
        try:
            await page.wait_for_event("dialog", timeout=20000)
        except PlaywrightTimeoutError:
            print(f"No dialog was triggered within 20 seconds for task_id: {task_id}")
        await browser.close()



# For the user to submit URL for testing. 
@app.get("/test/{task_id}")
async def start_test(task_id: str, background_tasks: BackgroundTasks):
    # Embed the YouTube URL directly here.
    youtube_url = "https://www.youtube.com/watch?v=Xlaioa4Cg1U"  # Replace with your desired YouTube URL
    if task_id in tasks:
        return {"status": "Task ID Already exists"}
    tasks[task_id] = {"status": "pending"}
    background_tasks.add_task(run_test_in_background, task_id, youtube_url)
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
