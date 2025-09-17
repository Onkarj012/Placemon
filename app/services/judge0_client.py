import requests
import os, time, logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()

log = logging.getLogger("judge0")
JUDGE0_URL = "https://judge0-ce.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv("x-rapidapi-key")


HEADERS = {
    "content-type": "application/json",
    "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    "X-RapidAPI-Key": RAPIDAPI_KEY
}

SUBMIT_URL = JUDGE0_URL.rstrip("/") + "/submissions?base64_encoded=false&wait=true"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def execute_code(src_code: str, language_id: int, stdin: str = "", expected_output: str = "") -> dict:
    """
    Submits code to Judge0 and fetches the result.
    """
    payload = {
        "source_code": src_code,
        "language_id": language_id,
        "stdin": stdin
    }

    res = requests.post(SUBMIT_URL, json=payload, headers=HEADERS)
    res.raise_for_status()

    try:
        result = res.json()
    except Exception:
        return {"error": "Invalid response", "status_code": res.status_code}

    if res.status_code not in [200, 201]:
        return {"error": "Submission failed", "details": result}
    
    return result