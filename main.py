from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import asyncio
import random
from openai import OpenAI
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import os
import base64
import json
import time
load_dotenv()

app = FastAPI()
tasks = {}  # In-memory storage for tasks (task_id -> status)
client = OpenAI()

async def run_test_in_background(task_id: str, url: str):
    # Note current time in SGT timezone in the format of YYYY-MM-DD HH:MM:SS
    starting_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    os.makedirs("screenshots", exist_ok=True)  # Ensure the screenshots directory exists
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://video-converter.com/")
        await page.wait_for_load_state("networkidle")
        
        async def on_dialog(dialog):
            custom_functions = [
                {
                    "type": "function",
                    "function": {
                        "name": "Extract_Conversion_Result",
                        "description": "Extracts the video conversion result including status, explanation, and reason. Returns an object with 'status' (boolean), 'explanation' (string), and 'reason' (string).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "status": {
                                    "type": "boolean",
                                    "description": "Tells whether the video conversion succeeded or didn't."
                                },
                                "explanation": {
                                    "type": "string",
                                    "description": "If it failed, explain why, else put as 'It can convert!'"
                                },
                                "solution": {
                                    "type": "string",
                                    "description": "Explain how to fix the issue if it failed (in the context it was a failed URL upload), else put as 'No solution needed.'"
                                }
                            },
                            "required": ["status", "explanation", "solution"]
                        }
                    }
                }
            ]
            await dialog.accept(url)
            await page.wait_for_timeout(10000)
            screenshot_path = f"screenshots/{task_id}.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved at {screenshot_path} for task_id: {task_id}")
            
            with open(screenshot_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            data_url = f"data:image/png;base64,{base64_image}"
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Analyse the test result of this video conversion website"},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    ],
                    tools=custom_functions,
                )
                arguments_json = response.choices[0].message.tool_calls[0].function.arguments
                output = json.loads(arguments_json)
                conversion_result = {
                    key: output.get(key)
                    for key in ["status","explanation", "solution"]
                }
                ending_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                final_output = {
                    "test_id": task_id,
                    "video_url": url,
                    "success_status": conversion_result["status"],
                    "starting_time": starting_time,
                    "screenshot_path": "/image/" + task_id,
                    "ending_time": ending_time,
                    "ai_analysis": conversion_result
                }
                tasks[task_id] = {"status": "done", "details": final_output}
            except Exception as e:
                print("Error during image analysis:", e)
            
        page.on("dialog", on_dialog)
        # tasks[task_id] = {"status": "Success", "details": {"screenshot_path": f"screenshots/{task_id}.png"}}
        await page.click("text=URL")
        print(f"Clicked on URL button for task_id: {task_id}")
        try:
            await page.wait_for_event("dialog", timeout=20000)
        except PlaywrightTimeoutError:
            print(f"No dialog was triggered within 20 seconds for task_id: {task_id}")
        await browser.close()



# For the user to submit URL for testing. 
@app.get("/test/{task_id}")
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


@app.get("/image/{task_id}")
async def get_image(task_id: str):
    screenshot_path = f"screenshots/{task_id}.png"
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(screenshot_path, media_type="image/png")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
