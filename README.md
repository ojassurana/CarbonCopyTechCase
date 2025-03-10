# Video Converter Test API

This is a RESTful API built with FastAPI to test the video conversion functionality of https://video-converter.com/ using Playwright and OpenAI's LLM. It triggers tests with a YouTube URL, stores results, generates enhanced reports, and handles errors.

## Installation

1. **Clone the Repository**:
   - `git clone <repository-url>` (replace with your repo URL if applicable).
   - `cd video-converter-test-api`

2. **Install Requirements**:
   - Create a virtual environment (optional): `python -m venv venv`
   - Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
   - Install dependencies: `pip install -r requirements.txt`

3. **Install Playwright Browser Binaries**:
- Run: `playwright install` to download the required browser binaries.

4. **Set Up Environment**:
- Create a `.env` file in the root directory.
- Add your OpenAI API key: `OPENAI_API_KEY=your-api-key-here`

## Running the API

- Start the server: `python script.py`
- The API will run on `http://0.0.0.0:8000`

## API Endpoints

### 1. Start a Test
- **Endpoint**: `GET /test/{task_id}`
- **Parameters**:
- `task_id` (path): A unique identifier (e.g., `4r434r`).
- `url` (query): The YouTube URL to test (e.g., `https://www.youtube.com/watch?v=9bZkp7q19f0`).
- **Response**:
- `{"status": "pending"}` if the task starts.
- `{"status": "Task ID Already exists"}` if the `task_id` is already in use.
- **Example**:
- `curl -X GET "http://localhost:8000/test/4r434r?url=https://www.youtube.com/watch?v=9bZkp7q19f0"`

### 2. Get Test Result
- **Endpoint**: `GET /result/{task_id}`
- **Parameters**:
- `task_id` (path): The task identifier.
- **Response**:
- `{"status": "pending"}` if the task is still running.
- `{"status": "done", "details": {...}}` with test details (e.g., `test_id`, `video_url`, `success_status`, `starting_time`, `ending_time`, `screenshot_path`, `ai_analysis`) when complete.
- **Example**:
- `curl "http://localhost:8000/result/4r434r"` (wait ~15 seconds or poll)

### 3. Get Screenshot
- **Endpoint**: `GET /image/{task_id}`
- **Parameters**:
- `task_id` (path): The task identifier.
- **Response**:
- Returns the screenshot image (`screenshots/{task_id}.png`) if found.
- `404` error if the image is not found.
- **Example**:
- `curl "http://localhost:8000/image/4r434r" -o screenshot.png`

## How It Works

1. **Test Initiation**:
- Send a GET request to `/test/{task_id}` with a `url` query parameter. The API queues the test as a background task.
- **Example with YouTube URL**:
- `curl -X GET "http://localhost:8000/test/test123?url=https://www.youtube.com/watch?v=9bZkp7q19f0"`
- This initiates a test with `task_id=test123` using the YouTube URL for "Gangnam Style" by PSY.

2. **Test Execution**:
- Playwright navigates to `https://video-converter.com/`, clicks the "URL" button, and handles the dialog by inputting the provided URL.
- Waits 10 seconds, takes a screenshot, and analyzes it using OpenAI’s `gpt-4o-mini` to determine the conversion result.

3. **Result Storage**:
- Stores the test status, details, and screenshot path in memory.

4. **Result Retrieval**:
- Use `/result/{task_id}` to get the test outcome, including AI-generated analysis.
- Use `/image/{task_id}` to download the screenshot.

## Notes
- The test outcome (`success_status`) and analysis depend on the website’s response and OpenAI’s interpretation of the screenshot.
- If no dialog appears within 20 seconds, the task fails.
- Ensure the `screenshots` directory has write permissions.

Happy testing!
