import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
  # should show first 10 chars, not None


def generate_question(topic: str, difficulty: str = "medium"):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # required by OpenRouter
        "X-Title": "PlacementPrepAI"              # your app name
    }


    prompt = f"""
    Generate a placement-style coding question.
    Topic: {topic}
    Difficulty: {difficulty}
    Format the response strictly as JSON with:
    - title (string)
    - description (string)
    - input_format (string)
    - output_format (string)
    - constraints (string)
    - sample_testcases (list of objects with input and output)
    """

    payload = {
        "model": "deepseek/deepseek-r1-0528:free",  # can change to specific one later
        "messages": [
            {"role": "system", "content": "You are a question generator for placement exams."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(BASE_URL, headers=headers, json=payload)
    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return {"error": str(e), "raw": data}
