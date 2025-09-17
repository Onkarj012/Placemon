# app/services/feedback_client.py
import os, httpx, json
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}

FEEDBACK_SYSTEM = (
    "You are a helpful coding tutor. A student submitted code and some testcases failed. "
    "Provide concise debugging hints that lead the student to the bug but DO NOT give full correct code. "
    "Output plain text only (no JSON)."
)

def request_feedback(payload: dict) -> str:
    """
    payload contains: question_title, failed_tests (list with index, stdin, stdout, stderr), language_id, source_code
    """
    user_text = (
        f"Question: {payload.get('question_title')}\n"
        f"Source code:\n{payload.get('source_code')}\n\n"
        f"Failed tests (do not reveal expected hidden outputs):\n"
    )
    for ft in payload.get("failed_tests", []):
        user_text += f"- Test #{ft['index']} | input: {ft['stdin']!r} | stdout: {ft['stdout']!r} | stderr: {ft['stderr']!r}\n"
    user_text += (
        "\nGive 2 short hints (1-2 sentences each) explaining likely causes and a final short suggestion on what to check next. "
        "Do NOT give full code or exact solution. Keep answer under 150 words."
    )

    body = {
        "model": os.getenv("OR_MODEL", "openrouter/auto"),
        "messages": [
            {"role": "system", "content": FEEDBACK_SYSTEM},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }
    r = httpx.post(OR_URL, headers=HEADERS, json=body, timeout=15.0)
    r.raise_for_status()
    j = r.json()
    return j["choices"][0]["message"]["content"].strip()
