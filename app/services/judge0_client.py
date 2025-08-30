import requests
import os
from dotenv import load_dotenv

load_dotenv()

JUDGE0_URL = "https://judge0-ce.p.rapidapi.com/submissions"
RAPIDAPI_KEY = os.getenv("x-rapidapi-key")


HEADERS = {
    "content-type": "application/json",
    "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    "X-RapidAPI-Key": RAPIDAPI_KEY
}

def execute_code(src_code: str, language_id: int, stdin: str = ""):
    """
    Submits code to Judge0 and fetches the result.
    """
    payload = {
        "source_code": src_code,
        "language_id": language_id,
        "stdin": stdin
    }

    res = requests.post(JUDGE0_URL + "?base64_encoded=false&wait=true", json=payload, headers=HEADERS)

    try:
        result = res.json()
    except Exception:
        return {"error": "Invalid response", "status_code": res.status_code}

    if res.status_code not in [200, 201]:
        return {"error": "Submission failed", "details": result}
    
    return res.json()