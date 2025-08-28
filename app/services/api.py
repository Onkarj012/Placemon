import os, json, time
import httpx
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
from app.models.questions_model import CodingQuestion, AptitudeQuestion
from pydantic import ValidationError
from uuid import uuid4

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = os.getenv("OR_MODEL")
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type":"application/json",
    "HTTP-Referer":"http://localhost"
}

def _make_system_prompt(qtype: str) -> str:
    if qtype == "coding":
        return (
            "You are a strict placement coding question generator.\n"
            "Always respond with VALID JSON ONLY, no text outside JSON.\n"
            "The JSON MUST strictly follow this schema:\n"
            "{\n"
            "  'id': string (UUID),\n"
            "  'title': string,\n"
            "  'description': string,\n"
            "  'topics': [string, string],\n"
            "  'input_format': string,\n"
            "  'output_format': string,\n"
            "  'constraints': string,\n"
            "  'sample_testcases': [ { 'input': string, 'output': string } ],\n"
            "  'hidden_testcases': [ { 'input': string, 'output': string } ],\n"
            "  'estimated_time_min': integer,\n"
            "  'hints': [string, string],\n"
            "  'canonical_solution': string (clear pseudocode or Python code)\n"
            "}\n\n"
            "Rules:\n"
            "- Always generate exactly 2 sample_testcases.\n"
            "- For easy: 4 hidden_testcases, medium/hard: 6 hidden_testcases.\n"
            "- Always include at least 2 relevant 'topics' (e.g., arrays, sorting).\n"
            "- estimated_time_min: easy=10–15, medium=20–30, hard=40–60.\n"
            "- Always include exactly 2 helpful hints.\n"
            "- canonical_solution: should be short and correct, not verbose.\n"
            "- Use realistic constraints like array size, time limits.\n"
            "- DO NOT include explanations, markdown, or text outside JSON."
        )
    else:  # aptitude
        return (
            "You are a strict aptitude question generator for placement preparation.\n"
            "Always respond with VALID JSON ONLY, no text outside JSON.\n"
            "The JSON MUST strictly follow this schema:\n"
            "{\n"
            "  'id': string (UUID),\n"
            "  'question_type': string ('mcq' or 'short_answer'),\n"
            "  'topic': string,\n"
            "  'difficulty': string ('easy', 'medium', 'hard'),\n"
            "  'question_text': string,\n"
            "  'options': [string, string, string, string] (required if question_type='mcq'),\n"
            "  'correct_option_index': integer 0–3 (required if question_type='mcq'),\n"
            "  'short_answer': string (required if question_type='short_answer'),\n"
            "  'step_by_step_solution': [string, string, ...],\n"
            "  'final_answer_explanation': string,\n"
            "  'hints': [string, string],\n"
            "  'estimated_time_sec': integer\n"
            "}\n\n"
            "Rules:\n"
            "- If MCQ, always generate exactly 4 options.\n"
            "- correct_option_index must match the index of the right option (0-based).\n"
            "- step_by_step_solution: explain each step clearly.\n"
            "- final_answer_explanation: short but clear.\n"
            "- hints: always 2.\n"
            "- estimated_time_sec: easy=60–90, medium=120–180, hard=240–300.\n"
            "- Do NOT include commentary, markdown, or text outside JSON."
        )



    
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _call_openrouter(messages: list, response_format: bool = False) -> str:
    body = {
        "model": OR_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1200
    }
    if response_format:
        body["response_format"] = {"type": "json_object"}

    r = httpx.post(OR_URL, headers=HEADERS, json=body, timeout=30.0)
    if r.status_code == 400 and response_format:
        # retry without response_format
        return _call_openrouter(messages, response_format=False)
    r.raise_for_status()
    j = r.json()
    content = j["choices"][0]["message"]["content"].strip()

    # try to clean if model wrapped JSON in text
    if not content.startswith("{"):
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end+1]

    return content

def _safe_json_loads(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try repair
        raw2 = _attempt_repair(raw, schema_name="question")
        return json.loads(raw2)


def _attempt_repair(raw: str, schema_name: str) -> str:
    """
    Ask the model to convert the raw text into valid JSON that follows the schema.
    Only one repair attempt allowed.
    """
    repair_prompt = (
        "Previous response was not valid JSON. Re-emit ONLY the JSON object conforming to the required schema. "
        "Do NOT add commentary.\n\nPrevious output:\n" + raw
    )
    messages = [{"role": "system", "content": f"Repair output to conform to {schema_name} schema."},
                {"role": "user", "content": repair_prompt}]
    return _call_openrouter(messages, response_format=False)

def generate_question(question_type: str, topic: str, difficulty: str = "medium") -> dict:
    """
    question_type: 'coding' or 'aptitude'
    returns a dict conforming to appropriate pydantic model
    """
    system = _make_system_prompt(question_type)
    user_message = f"Topic: {topic}\nDifficulty: {difficulty}\nGenerate one {question_type} question now."

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message}
    ]

    raw = _call_openrouter(messages=messages, response_format=False)

    # Try to parse JSON
    try:
        parsed = parsed = _safe_json_loads(raw)
    except json.JSONDecodeError:
        # attempt repair once
        raw2 = _attempt_repair(raw, schema_name=question_type)
        try:
            parsed = json.loads(raw2)
            raw = raw2
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM. Raw1: {raw!r}, Raw2: {raw2!r}") from e

    # Validate with pydantic
    try:
        if question_type == "coding":
            # ensure id present
            if "id" not in parsed:
                parsed["id"] = str(uuid4())
            q = CodingQuestion(**parsed)
            return q.model_dump()
        else:
            if "id" not in parsed:
                parsed["id"] = str(uuid4())
            q = AptitudeQuestion(**parsed)
            return q.model_dump()
    except ValidationError as ve:
        # give a useful error for debugging
        raise ValueError(f"LLM output failed validation: {ve}\nRaw JSON: {json.dumps(parsed, indent=2)}")
