import os, httpx, json
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = os.getenv("OR_MODEL")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type":"application/json",
    "HTTP-Referer":"http://localhost"
}

body = {
    "model": OR_MODEL,
    "messages": [{"role":"user", "content":"Say hello"}],
}

r = httpx.post(url, headers=headers, json=body)
print(r.status_code, r.text)
